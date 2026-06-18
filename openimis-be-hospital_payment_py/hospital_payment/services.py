import logging
import uuid as uuid_lib
from datetime import datetime
from decimal import Decimal

from django.db import transaction
from django.utils.translation import gettext as _
from django.core.exceptions import PermissionDenied, ValidationError

from claim.models import Claim
from location.models import HealthFacility
from core.utils import TimeUtils

from .models import (
    HospitalPaymentBatch,
    HospitalPaymentBatchClaim,
    HospitalPaymentRecord,
)
from .apps import HospitalPaymentConfig

logger = logging.getLogger(__name__)


def validate_claims_for_payment(claims):
    """
    Payment-readiness validation only.
    Does NOT re-validate medical eligibility (that's already done by claim/validations.py).

    Checks:
    - Claim status = VALUATED (16)
    - Claim not already in a pending/approved/processing batch
    - Claim has a remunerated amount > 0
    - Claim's health facility has an acc_code (bank account reference)
    """
    errors = []
    for claim in claims:
        if claim.status != Claim.STATUS_VALUATED:
            errors.append(
                {
                    "claim_code": claim.code,
                    "error": f"Claim {claim.code} is not valuated (status={claim.status})",
                }
            )
            continue

        existing = HospitalPaymentBatchClaim.objects.filter(
            claim=claim,
            validity_to__isnull=True,
            payment_batch__status__in=[
                HospitalPaymentBatch.STATUS_PENDING,
                HospitalPaymentBatch.STATUS_APPROVED,
                HospitalPaymentBatch.STATUS_PROCESSING,
            ],
        ).exists()
        if existing:
            errors.append(
                {
                    "claim_code": claim.code,
                    "error": f"Claim {claim.code} is already in an active payment batch",
                }
            )
            continue

        if claim.remunerated is None or claim.remunerated <= 0:
            errors.append(
                {
                    "claim_code": claim.code,
                    "error": f"Claim {claim.code} has no remunerated amount",
                }
            )
            continue

        hf = claim.health_facility
        if not hf.acc_code:
            errors.append(
                {
                    "claim_code": claim.code,
                    "error": f"HF {hf.code} has no bank account code (AccCode)",
                }
            )
            continue

    return errors


@transaction.atomic
def create_payment_batches(user, health_facility_ids=None):
    """
    Collects all STATUS_VALUATED claims not yet in a batch and groups them
    by Health Facility into HospitalPaymentBatch records.

    Args:
        user: The InteractiveUser creating the batches
        health_facility_ids: Optional list of HF IDs to filter by. If None, all HFs.

    Returns:
        List of created HospitalPaymentBatch objects
    """
    audit_user_id = getattr(user, "id_for_audit", -1)

    # Get all valuated claims not already in a batch
    queryset = Claim.objects.filter(
        status=Claim.STATUS_VALUATED,
        validity_to__isnull=True,
    )

    if health_facility_ids:
        queryset = queryset.filter(health_facility_id__in=health_facility_ids)

    # Exclude claims already in active batches
    existing_claim_ids = HospitalPaymentBatchClaim.objects.filter(
        validity_to__isnull=True,
        payment_batch__status__in=[
            HospitalPaymentBatch.STATUS_PENDING,
            HospitalPaymentBatch.STATUS_APPROVED,
            HospitalPaymentBatch.STATUS_PROCESSING,
        ],
    ).values_list("claim_id", flat=True)
    queryset = queryset.exclude(id__in=existing_claim_ids)

    # Group by health facility
    claims_by_hf = {}
    for claim in queryset.select_related("health_facility", "insuree"):
        hf_id = claim.health_facility_id
        if hf_id not in claims_by_hf:
            claims_by_hf[hf_id] = []
        claims_by_hf[hf_id].append(claim)

    # Validate claims
    all_claims = [claim for claims in claims_by_hf.values() for claim in claims]
    validation_errors = validate_claims_for_payment(all_claims)
    if validation_errors:
        # Filter out invalid claims
        invalid_codes = {e["claim_code"] for e in validation_errors}
        for hf_id in claims_by_hf:
            claims_by_hf[hf_id] = [
                c for c in claims_by_hf[hf_id] if c.code not in invalid_codes
            ]
        # Remove empty HFs
        claims_by_hf = {k: v for k, v in claims_by_hf.items() if v}

    if not claims_by_hf:
        logger.info("No valuated claims available for batch creation")
        return []

    created_batches = []
    now = TimeUtils.now()

    for hf_id, claims in claims_by_hf.items():
        hf = claims[0].health_facility
        min_claims = HospitalPaymentConfig.min_claims_per_batch
        if len(claims) < min_claims:
            logger.info(
                f"Skipping HF {hf.code}: only {len(claims)} claims "
                f"(minimum: {min_claims})"
            )
            continue

        batch_code = f"HPB-{hf.code}-{now.strftime('%Y%m%d%H%M%S')}-{uuid_lib.uuid4().hex[:6].upper()}"
        total_amount = sum(
            (c.remunerated or Decimal(0)) for c in claims
        )

        batch = HospitalPaymentBatch.objects.create(
            health_facility=hf,
            batch_code=batch_code,
            total_amount=total_amount,
            total_claims=len(claims),
            status=HospitalPaymentBatch.STATUS_PENDING,
            audit_user_id=audit_user_id,
            validity_from=now,
        )

        for claim in claims:
            HospitalPaymentBatchClaim.objects.create(
                payment_batch=batch,
                claim=claim,
                claim_code=claim.code,
                amount=claim.remunerated or Decimal(0),
                status=HospitalPaymentBatchClaim.STATUS_PENDING,
                audit_user_id=audit_user_id,
                validity_from=now,
            )

        created_batches.append(batch)
        logger.info(
            f"Created payment batch {batch_code} for HF {hf.code} "
            f"with {len(claims)} claims, total: {total_amount}"
        )

    return created_batches


@transaction.atomic
def approve_payment_batch(user, batch_ids):
    """
    Admin approves one or more payment batches for processing.
    Sets status to APPROVED and triggers async payment processing.

    Args:
        user: The InteractiveUser approving the batches
        batch_ids: List of HospitalPaymentBatch IDs to approve

    Returns:
        List of approved HospitalPaymentBatch objects
    """
    audit_user_id = getattr(user, "id_for_audit", -1)
    now = TimeUtils.now()

    batches = HospitalPaymentBatch.objects.filter(
        id__in=batch_ids,
        status=HospitalPaymentBatch.STATUS_PENDING,
        validity_to__isnull=True,
    )

    if not batches.exists():
        raise ValidationError(_("No pending payment batches found to approve"))

    approved = []
    for batch in batches:
        batch.status = HospitalPaymentBatch.STATUS_APPROVED
        # user._u is the InteractiveUser, which is what approved_by FK expects
        batch.approved_by = getattr(user, "_u", user)
        batch.approved_date = now
        batch.audit_user_id = audit_user_id
        batch.save()
        approved.append(batch)
        logger.info(f"Payment batch {batch.batch_code} approved by user {audit_user_id}")

    return approved


def send_payment_to_api(batch):
    """
    Sends the payment batch to the external payment API.
    Constructs the request payload and calls the API.

    Args:
        batch: HospitalPaymentBatch instance (must be APPROVED status)

    Returns:
        dict: The API response

    Raises:
        Exception: If the API call fails
    """
    import requests

    api_url = HospitalPaymentConfig.payment_api_url
    api_key = HospitalPaymentConfig.payment_api_key
    timeout = HospitalPaymentConfig.payment_api_timeout

    if not api_url:
        raise ValueError("Payment API URL is not configured")

    # Build payload
    batch_claims = batch.batch_claims.filter(
        validity_to__isnull=True,
        status=HospitalPaymentBatchClaim.STATUS_PENDING,
    ).select_related("claim", "claim__insuree")

    payload = {
        "batch_reference": batch.batch_code,
        "batch_uuid": str(batch.uuid),
        "health_facility": {
            "code": batch.health_facility.code,
            "name": batch.health_facility.name,
            "acc_code": batch.health_facility.acc_code,
        },
        "total_amount": str(batch.total_amount),
        "total_claims": batch.total_claims,
        "claims": [
            {
                "claim_id": bc.claim_id,
                "claim_code": bc.claim_code,
                "amount": str(bc.amount),
                "insuree_chfid": bc.claim.insuree.chf_id if bc.claim.insuree else None,
            }
            for bc in batch_claims
        ],
    }

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    logger.info(f"Sending payment batch {batch.batch_code} to payment API at {api_url}")

    response = requests.post(
        api_url,
        json=payload,
        headers=headers,
        timeout=timeout,
    )
    response.raise_for_status()

    api_response = response.json()
    logger.info(
        f"Payment API responded for batch {batch.batch_code}: {api_response}"
    )

    return api_response


@transaction.atomic
def process_payment_response(batch, api_response):
    """
    Processes the response from the payment API after sending a batch.
    Updates batch status and creates payment records.

    Args:
        batch: HospitalPaymentBatch instance
        api_response: dict response from payment API
    """
    now = TimeUtils.now()
    audit_user_id = batch.audit_user_id

    # Store raw response
    batch.payment_api_response = api_response

    api_status = api_response.get("status", "").upper()
    api_reference = api_response.get("payment_reference") or api_response.get("reference")
    if api_reference:
        batch.payment_api_reference = api_reference

    if api_status in ("PAID", "SUCCESS", "COMPLETED"):
        batch.status = HospitalPaymentBatch.STATUS_PAID
        batch.paid_date = now

        # Update individual claim statuses
        paid_claim_ids = api_response.get("claims_paid", [])
        batch_claims = batch.batch_claims.filter(validity_to__isnull=True)
        for bc in batch_claims:
            if not paid_claim_ids or bc.claim_id in paid_claim_ids:
                bc.status = HospitalPaymentBatchClaim.STATUS_PAID
                bc.payment_reference = api_reference
                bc.save()

        total_paid = Decimal(str(api_response.get("total_paid_amount", batch.total_amount)))
        paid_count = len(paid_claim_ids) if paid_claim_ids else batch_claims.count()
        failed_count = batch_claims.count() - paid_count

    elif api_status in ("PARTIAL", "PARTIALLY_PAID"):
        batch.status = HospitalPaymentBatch.STATUS_PARTIALLY_PAID
        batch.paid_date = now

        paid_claim_ids = api_response.get("claims_paid", [])
        failed_claim_ids = api_response.get("claims_failed", [])
        batch_claims = batch.batch_claims.filter(validity_to__isnull=True)

        for bc in batch_claims:
            if bc.claim_id in paid_claim_ids:
                bc.status = HospitalPaymentBatchClaim.STATUS_PAID
                bc.payment_reference = api_reference
            elif bc.claim_id in failed_claim_ids:
                bc.status = HospitalPaymentBatchClaim.STATUS_FAILED
                bc.failure_reason = api_response.get("failure_reason", "")
            bc.save()

        total_paid = Decimal(
            str(api_response.get("total_paid_amount", 0))
        )
        paid_count = len(paid_claim_ids)
        failed_count = len(failed_claim_ids)

    elif api_status in ("FAILED", "ERROR", "REJECTED"):
        batch.status = HospitalPaymentBatch.STATUS_FAILED
        batch.failure_reason = api_response.get("message", "Payment API returned failure")

        batch_claims = batch.batch_claims.filter(validity_to__isnull=True)
        for bc in batch_claims:
            bc.status = HospitalPaymentBatchClaim.STATUS_FAILED
            bc.failure_reason = batch.failure_reason
            bc.save()

        total_paid = Decimal("0")
        paid_count = 0
        failed_count = batch_claims.count()

    else:
        # Unknown status - keep processing
        batch.status = HospitalPaymentBatch.STATUS_PROCESSING
        total_paid = Decimal("0")
        paid_count = 0
        failed_count = 0

    batch.save()

    # Create payment record
    HospitalPaymentRecord.objects.create(
        payment_batch=batch,
        payment_api_reference=api_reference,
        total_paid_amount=total_paid,
        claims_paid_count=paid_count,
        claims_failed_count=failed_count,
        status=api_status or "UNKNOWN",
        raw_response=api_response,
        received_date=now,
        audit_user_id=audit_user_id,
        validity_from=now,
    )

    logger.info(
        f"Processed payment response for batch {batch.batch_code}: "
        f"status={batch.status}, paid={paid_count}, failed={failed_count}"
    )

    return batch


@transaction.atomic
def process_webhook_payment_confirmation(webhook_data):
    """
    Processes payment confirmation received via webhook from the payment API.
    This is called without human intervention when the payment API sends
    a callback/notification.

    Args:
        webhook_data: dict containing:
            - batch_reference: The batch code
            - payment_reference: Reference from payment API
            - status: Payment status (PAID/PARTIAL/FAILED)
            - total_paid_amount: Total amount paid
            - claims_paid: List of claim IDs that were paid
            - claims_failed: List of claim IDs that failed
            - raw_response: Full raw response

    Returns:
        HospitalPaymentBatch: The updated batch
    """
    batch_reference = webhook_data.get("batch_reference")
    if not batch_reference:
        raise ValueError("batch_reference is required")

    batch = HospitalPaymentBatch.objects.filter(
        batch_code=batch_reference,
        validity_to__isnull=True,
    ).first()

    if not batch:
        raise ValueError(f"Payment batch {batch_reference} not found")

    return process_payment_response(batch, webhook_data)
