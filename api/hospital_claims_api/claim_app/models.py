import uuid
from decimal import Decimal

from django.db import models
from django.conf import settings


class Claim(models.Model):
    STATUS_ENTERED = "ENTERED"
    STATUS_CHECKED = "CHECKED"
    STATUS_PROCESSED = "PROCESSED"
    STATUS_VALUATED = "VALUATED"
    STATUS_REJECTED = "REJECTED"

    STATUS_CHOICES = [
        (STATUS_ENTERED, "Entered"),
        (STATUS_CHECKED, "Checked"),
        (STATUS_PROCESSED, "Processed"),
        (STATUS_VALUATED, "Valuated"),
        (STATUS_REJECTED, "Rejected"),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    code = models.CharField(max_length=50, unique=True)
    insuree = models.ForeignKey(
        "insuree.Insuree", on_delete=models.CASCADE, related_name="claims"
    )
    health_facility = models.ForeignKey(
        "location.HealthFacility", on_delete=models.CASCADE, related_name="claims"
    )
    diagnosis = models.ForeignKey(
        "medical.Diagnosis", on_delete=models.SET_NULL, null=True, blank=True
    )
    date_from = models.DateField()
    date_to = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ENTERED)
    claimed = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal("0"))
    remunerated = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "claim_app_claim"
        ordering = ["-created_at"]

    def __str__(self):
        return self.code


class ClaimItem(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    claim = models.ForeignKey(Claim, on_delete=models.CASCADE, related_name="items")
    item = models.ForeignKey(
        "medical.Item", on_delete=models.SET_NULL, null=True, blank=True
    )
    qty_claimed = models.PositiveIntegerField(default=1)
    price_claimed = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal("0"))
    remunerated_amount = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = "claim_app_claim_item"

    def __str__(self):
        return f"{self.claim.code} - Item #{self.id}"


class ClaimService(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    claim = models.ForeignKey(Claim, on_delete=models.CASCADE, related_name="services")
    service = models.ForeignKey(
        "medical.Service", on_delete=models.SET_NULL, null=True, blank=True
    )
    qty_claimed = models.PositiveIntegerField(default=1)
    price_claimed = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal("0"))
    remunerated_amount = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = "claim_app_claim_service"

    def __str__(self):
        return f"{self.claim.code} - Service #{self.id}"
