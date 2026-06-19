import uuid
from decimal import Decimal

from django.db import models
from django.conf import settings


class HospitalPaymentBatch(models.Model):
    STATUS_PENDING = "PENDING"
    STATUS_APPROVED = "APPROVED"
    STATUS_PROCESSING = "PROCESSING"
    STATUS_PAID = "PAID"
    STATUS_PARTIALLY_PAID = "PARTIALLY_PAID"
    STATUS_FAILED = "FAILED"
    STATUS_REJECTED = "REJECTED"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_PROCESSING, "Processing"),
        (STATUS_PAID, "Paid"),
        (STATUS_PARTIALLY_PAID, "Partially Paid"),
        (STATUS_FAILED, "Failed"),
        (STATUS_REJECTED, "Rejected"),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    batch_code = models.CharField(max_length=100, unique=True)
    health_facility = models.ForeignKey(
        "location.HealthFacility", on_delete=models.CASCADE, related_name="payment_batches"
    )
    total_amount = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal("0"))
    total_claims = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="created_batches"
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="approved_batches"
    )
    approved_date = models.DateTimeField(null=True, blank=True)
    paid_date = models.DateTimeField(null=True, blank=True)
    payment_api_reference = models.CharField(max_length=200, blank=True, default="")
    payment_api_response = models.JSONField(null=True, blank=True)
    failure_reason = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "hospital_payment_batch"
        ordering = ["-created_at"]

    def __str__(self):
        return self.batch_code


class HospitalPaymentBatchClaim(models.Model):
    STATUS_PENDING = "PENDING"
    STATUS_PAID = "PAID"
    STATUS_FAILED = "FAILED"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_PAID, "Paid"),
        (STATUS_FAILED, "Failed"),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    payment_batch = models.ForeignKey(
        HospitalPaymentBatch, on_delete=models.CASCADE, related_name="batch_claims"
    )
    claim = models.ForeignKey(
        "claim_app.Claim", on_delete=models.SET_NULL, null=True, blank=True
    )
    claim_code = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal("0"))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    payment_reference = models.CharField(max_length=200, blank=True, default="")
    failure_reason = models.TextField(blank=True, default="")

    class Meta:
        db_table = "hospital_payment_batch_claim"

    def __str__(self):
        return f"{self.payment_batch.batch_code} - {self.claim_code}"


class HospitalPaymentRecord(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    payment_batch = models.ForeignKey(
        HospitalPaymentBatch, on_delete=models.CASCADE, related_name="payment_records"
    )
    payment_api_reference = models.CharField(max_length=200, blank=True, default="")
    total_paid_amount = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal("0"))
    claims_paid_count = models.PositiveIntegerField(default=0)
    claims_failed_count = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=50, blank=True, default="")
    raw_response = models.JSONField(null=True, blank=True)
    received_date = models.DateTimeField()

    class Meta:
        db_table = "hospital_payment_record"
        ordering = ["-received_date"]

    def __str__(self):
        return f"Record for {self.payment_batch.batch_code} - {self.status}"
