import logging

from celery import shared_task
from django.db import transaction

from .models import HospitalPaymentBatch
from .services import send_payment_to_api, process_payment_response

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_payment_batch_task(self, batch_id):
    """
    Async task to send an approved payment batch to the external payment API.
    Called automatically after admin approves a batch.

    Flow:
    1. Load the batch (must be APPROVED status)
    2. Set status to PROCESSING
    3. Call the payment API
    4. Process the response (updates batch + creates payment record)
    5. On failure, retry with exponential backoff

    Args:
        batch_id: HospitalPaymentBatch ID
    """
    try:
        batch = HospitalPaymentBatch.objects.filter(
            id=batch_id,
            validity_to__isnull=True,
        ).first()

        if not batch:
            logger.error(f"Payment batch {batch_id} not found")
            return

        if batch.status != HospitalPaymentBatch.STATUS_APPROVED:
            logger.warning(
                f"Payment batch {batch_id} is not approved (status={batch.status}), skipping"
            )
            return

        # Set to processing
        batch.status = HospitalPaymentBatch.STATUS_PROCESSING
        batch.save()

        logger.info(f"Processing payment batch {batch.batch_code} (ID: {batch_id})")

        # Send to payment API
        api_response = send_payment_to_api(batch)

        # Process the response
        with transaction.atomic():
            process_payment_response(batch, api_response)

        logger.info(
            f"Payment batch {batch.batch_code} processed successfully, "
            f"final status: {batch.status}"
        )

    except Exception as exc:
        logger.error(
            f"Error processing payment batch {batch_id}: {exc}", exc_info=True
        )

        # Mark batch as failed if all retries exhausted
        try:
            batch = HospitalPaymentBatch.objects.get(id=batch_id)
            batch.status = HospitalPaymentBatch.STATUS_FAILED
            batch.failure_reason = str(exc)
            batch.save()
        except Exception:
            pass

        # Retry with backoff
        raise self.retry(exc=exc)
