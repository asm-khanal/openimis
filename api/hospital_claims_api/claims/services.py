import logging
import uuid as uuid_lib
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from claim_app.models import Claim, ClaimItem, ClaimService
from hospital_payment.models import (
    HospitalPaymentBatch, HospitalPaymentBatchClaim, HospitalPaymentRecord,
)

logger = logging.getLogger(__name__)


def valuate_claim(claim):
    claim.status = Claim.STATUS_VALUATED
    total_remunerated = Decimal(0)
    for item in claim.items.all():
        amt = item.price_claimed
        item.remunerated_amount = amt
        item.save()
        total_remunerated += amt * item.qty_claimed
    for svc in claim.services.all():
        amt = svc.price_claimed
        svc.remunerated_amount = amt
        svc.save()
        total_remunerated += amt * svc.qty_claimed
    claim.remunerated = total_remunerated
    claim.save()
    return claim


@transaction.atomic
def create_payment_batches(user, health_facility_codes=None):
    queryset = Claim.objects.filter(status=Claim.STATUS_VALUATED)
    if health_facility_codes:
        queryset = queryset.filter(health_facility__code__in=health_facility_codes)
    existing_codes = HospitalPaymentBatchClaim.objects.filter(
        payment_batch__status__in=[
            HospitalPaymentBatch.STATUS_PENDING,
            HospitalPaymentBatch.STATUS_APPROVED,
            HospitalPaymentBatch.STATUS_PROCESSING,
        ],
    ).values_list("claim_code", flat=True)
    queryset = queryset.exclude(code__in=existing_codes)

    claims_by_hf = {}
    for claim in queryset.select_related("health_facility", "insuree"):
        hf_code = claim.health_facility.code
        claims_by_hf.setdefault(hf_code, []).append(claim)

    for hf_code, claims in list(claims_by_hf.items()):
        invalid = []
        for c in claims:
            if c.status != Claim.STATUS_VALUATED:
                invalid.append(c.code)
            elif c.remunerated is None or c.remunerated <= 0:
                invalid.append(c.code)
            elif not c.health_facility.acc_code:
                invalid.append(c.code)
        claims_by_hf[hf_code] = [c for c in claims if c.code not in invalid]
    claims_by_hf = {k: v for k, v in claims_by_hf.items() if v}

    if not claims_by_hf:
        return []

    created = []
    now = timezone.now()

    for hf_code, claims in claims_by_hf.items():
        hf = claims[0].health_facility
        if len(claims) < settings.MIN_CLAIMS_PER_BATCH:
            continue

        batch_code = f"HPB-{hf_code}-{now.strftime('%Y%m%d%H%M%S')}-{uuid_lib.uuid4().hex[:6].upper()}"
        total = sum((c.remunerated or Decimal(0)) for c in claims)

        batch = HospitalPaymentBatch.objects.create(
            batch_code=batch_code,
            health_facility=hf,
            total_amount=total,
            total_claims=len(claims),
            status=HospitalPaymentBatch.STATUS_PENDING,
            created_by=user,
        )

        for claim in claims:
            HospitalPaymentBatchClaim.objects.create(
                payment_batch=batch,
                claim=claim,
                claim_code=claim.code,
                amount=claim.remunerated or Decimal(0),
                status=HospitalPaymentBatchClaim.STATUS_PENDING,
            )

        created.append(batch)

    return created


@transaction.atomic
def approve_payment_batch(user, batch_ids):
    now = timezone.now()
    batches = HospitalPaymentBatch.objects.filter(
        id__in=batch_ids, status=HospitalPaymentBatch.STATUS_PENDING,
    )
    if not batches.exists():
        from django.core.exceptions import ValidationError
        raise ValidationError("No pending payment batches found to approve")

    approved = []
    for batch in batches:
        batch.status = HospitalPaymentBatch.STATUS_APPROVED
        batch.approved_by = user
        batch.approved_date = now
        batch.save()
        approved.append(batch)
    return approved


def send_payment_to_api(batch):
    import requests
    api_url = settings.PAYMENT_API_URL
    api_key = settings.PAYMENT_API_KEY
    timeout = settings.PAYMENT_API_TIMEOUT

    if not api_url:
        raise ValueError("Payment API URL is not configured")

    batch_claims = batch.batch_claims.filter(status=HospitalPaymentBatchClaim.STATUS_PENDING)
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
        "claims": [{"claim_code": bc.claim_code, "amount": str(bc.amount)} for bc in batch_claims],
    }

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    logger.info(f"Sending payment batch {batch.batch_code} to {api_url}")
    response = requests.post(api_url, json=payload, headers=headers, timeout=timeout)
    response.raise_for_status()
    return response.json()


@transaction.atomic
def process_payment_response(batch, api_response):
    now = timezone.now()
    batch.payment_api_response = api_response
    api_status = api_response.get("status", "").upper()
    api_reference = api_response.get("payment_reference") or api_response.get("reference")
    if api_reference:
        batch.payment_api_reference = api_reference

    if api_status in ("PAID", "SUCCESS", "COMPLETED"):
        batch.status = HospitalPaymentBatch.STATUS_PAID
        batch.paid_date = now
        paid_codes = api_response.get("claims_paid", [])
        for bc in batch.batch_claims.all():
            if not paid_codes or bc.claim_code in paid_codes:
                bc.status = HospitalPaymentBatchClaim.STATUS_PAID
                bc.payment_reference = api_reference
                bc.save()
        total_paid = Decimal(str(api_response.get("total_paid_amount", batch.total_amount)))
        paid_count = len(paid_codes) if paid_codes else batch.batch_claims.count()
        failed_count = batch.batch_claims.count() - paid_count
    elif api_status in ("PARTIAL", "PARTIALLY_PAID"):
        batch.status = HospitalPaymentBatch.STATUS_PARTIALLY_PAID
        batch.paid_date = now
        paid_codes = api_response.get("claims_paid", [])
        failed_codes = api_response.get("claims_failed", [])
        for bc in batch.batch_claims.all():
            if bc.claim_code in paid_codes:
                bc.status = HospitalPaymentBatchClaim.STATUS_PAID
                bc.payment_reference = api_reference
            elif bc.claim_code in failed_codes:
                bc.status = HospitalPaymentBatchClaim.STATUS_FAILED
                bc.failure_reason = api_response.get("failure_reason", "")
            bc.save()
        total_paid = Decimal(str(api_response.get("total_paid_amount", 0)))
        paid_count = len(paid_codes)
        failed_count = len(failed_codes)
    elif api_status in ("FAILED", "ERROR", "REJECTED"):
        batch.status = HospitalPaymentBatch.STATUS_FAILED
        batch.failure_reason = api_response.get("message", "Payment API returned failure")
        for bc in batch.batch_claims.all():
            bc.status = HospitalPaymentBatchClaim.STATUS_FAILED
            bc.failure_reason = batch.failure_reason
            bc.save()
        total_paid = Decimal("0")
        paid_count = 0
        failed_count = batch.batch_claims.count()
    else:
        batch.status = HospitalPaymentBatch.STATUS_PROCESSING
        total_paid = Decimal("0")
        paid_count = 0
        failed_count = 0

    batch.save()
    HospitalPaymentRecord.objects.create(
        payment_batch=batch, payment_api_reference=api_reference,
        total_paid_amount=total_paid, claims_paid_count=paid_count,
        claims_failed_count=failed_count, status=api_status or "UNKNOWN",
        raw_response=api_response, received_date=now,
    )
    return batch


@transaction.atomic
def process_webhook_payment_confirmation(webhook_data):
    ref = webhook_data.get("batch_reference")
    if not ref:
        raise ValueError("batch_reference is required")
    batch = HospitalPaymentBatch.objects.filter(batch_code=ref).first()
    if not batch:
        raise ValueError(f"Payment batch {ref} not found")
    return process_payment_response(batch, webhook_data)


def process_payment_batch(batch_id):
    try:
        batch = HospitalPaymentBatch.objects.filter(id=batch_id).first()
        if not batch or batch.status != HospitalPaymentBatch.STATUS_APPROVED:
            return
        batch.status = HospitalPaymentBatch.STATUS_PROCESSING
        batch.save()
        api_response = send_payment_to_api(batch)
        with transaction.atomic():
            process_payment_response(batch, api_response)
    except Exception as exc:
        logger.error(f"Error processing payment batch {batch_id}: {exc}", exc_info=True)
        try:
            b = HospitalPaymentBatch.objects.get(id=batch_id)
            b.status = HospitalPaymentBatch.STATUS_FAILED
            b.failure_reason = str(exc)
            b.save()
        except Exception:
            pass
        raise
