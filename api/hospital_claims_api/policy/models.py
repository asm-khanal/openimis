from django.db import models
from decimal import Decimal


class Policy(models.Model):
    STATUS_ACTIVE = "ACTIVE"
    STATUS_INACTIVE = "INACTIVE"
    STATUS_EXPIRED = "EXPIRED"
    STATUS_SUSPENDED = "SUSPENDED"

    STATUS_CHOICES = [
        (STATUS_ACTIVE, "Active"),
        (STATUS_INACTIVE, "Inactive"),
        (STATUS_EXPIRED, "Expired"),
        (STATUS_SUSPENDED, "Suspended"),
    ]

    STAGE_NEW = "NEW"
    STAGE_RENEWED = "RENEWED"
    STAGE_SUSPENDED = "SUSPENDED"

    STAGE_CHOICES = [
        (STAGE_NEW, "New"),
        (STAGE_RENEWED, "Renewed"),
        (STAGE_SUSPENDED, "Suspended"),
    ]

    family = models.ForeignKey(
        "insuree.Family", on_delete=models.CASCADE, null=True, blank=True
    )
    product = models.ForeignKey(
        "product.Product", on_delete=models.CASCADE, null=True, blank=True
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    stage = models.CharField(max_length=20, choices=STAGE_CHOICES, default=STAGE_NEW)
    enroll_date = models.DateField(null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    effective_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    value = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal("0"))

    class Meta:
        db_table = "policy_policy"

    def __str__(self):
        return f"Policy #{self.id}"
