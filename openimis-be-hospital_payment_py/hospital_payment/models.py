import uuid
import logging

from core import fields
from core import models as core_models
from django.db import models
from django.utils.translation import gettext_lazy as _
from location.models import HealthFacility

logger = logging.getLogger(__name__)


class HospitalPaymentBatch(core_models.VersionedModel):
    """
    Groups valuated claims by Health Facility for bulk payment processing.
    Created when admin triggers batch creation - collects all STATUS_VALUATED
    claims for a given Health Facility that haven't been assigned to a batch yet.
    """

    STATUS_PENDING = 1
    STATUS_APPROVED = 2
    STATUS_PROCESSING = 3
    STATUS_PAID = 4
    STATUS_PARTIALLY_PAID = 5
    STATUS_FAILED = 6
    STATUS_REJECTED = 7

    STATUS_CHOICES = (
        (STATUS_PENDING, _("Pending Approval")),
        (STATUS_APPROVED, _("Approved")),
        (STATUS_PROCESSING, _("Processing")),
        (STATUS_PAID, _("Paid")),
        (STATUS_PARTIALLY_PAID, _("Partially Paid")),
        (STATUS_FAILED, _("Failed")),
        (STATUS_REJECTED, _("Rejected")),
    )

    id = models.BigAutoField(db_column="HospitalPaymentBatchID", primary_key=True)
    uuid = models.CharField(
        db_column="HospitalPaymentBatchUUID",
        max_length=36,
        default=uuid.uuid4,
        unique=True,
    )

    health_facility = models.ForeignKey(
        HealthFacility,
        models.DO_NOTHING,
        db_column="HFID",
        related_name="hospital_payment_batches",
    )

    batch_code = models.CharField(
        db_column="BatchCode", max_length=50, unique=True
    )

    total_amount = models.DecimalField(
        db_column="TotalAmount", max_digits=18, decimal_places=2, default=0
    )
    total_claims = models.IntegerField(db_column="TotalClaims", default=0)

    status = models.SmallIntegerField(
        db_column="Status", default=STATUS_PENDING, choices=STATUS_CHOICES
    )

    approved_by = models.ForeignKey(
        core_models.InteractiveUser,
        models.DO_NOTHING,
        db_column="ApprovedBy",
        related_name="approved_hospital_payment_batches",
        blank=True,
        null=True,
    )
    approved_date = fields.DateTimeField(
        db_column="ApprovedDate", blank=True, null=True
    )

    paid_date = fields.DateTimeField(db_column="PaidDate", blank=True, null=True)

    payment_api_reference = models.CharField(
        db_column="PaymentApiReference", max_length=100, blank=True, null=True
    )

    payment_api_response = models.JSONField(
        db_column="PaymentApiResponse", blank=True, null=True
    )

    failure_reason = models.TextField(
        db_column="FailureReason", blank=True, null=True
    )

    audit_user_id = models.IntegerField(db_column="AuditUserID")

    class Meta:
        managed = True
        db_table = "tblHospitalPaymentBatch"

    def __str__(self):
        return (
            f"Batch {self.batch_code} - HF:{self.health_facility_id} "
            f"Amount:{self.total_amount} Status:{self.status}"
        )


class HospitalPaymentBatchClaim(core_models.VersionedModel):
    """
    Links individual claims to a HospitalPaymentBatch.
    Tracks per-claim payment status within the bulk payment.
    """

    STATUS_PENDING = 1
    STATUS_PAID = 2
    STATUS_FAILED = 3
    STATUS_EXCLUDED = 4

    STATUS_CHOICES = (
        (STATUS_PENDING, _("Pending")),
        (STATUS_PAID, _("Paid")),
        (STATUS_FAILED, _("Failed")),
        (STATUS_EXCLUDED, _("Excluded")),
    )

    id = models.BigAutoField(
        db_column="HospitalPaymentBatchClaimID", primary_key=True
    )
    uuid = models.CharField(
        db_column="HospitalPaymentBatchClaimUUID",
        max_length=36,
        default=uuid.uuid4,
        unique=True,
    )

    payment_batch = models.ForeignKey(
        HospitalPaymentBatch,
        models.DO_NOTHING,
        db_column="HospitalPaymentBatchID",
        related_name="batch_claims",
    )

    claim = models.ForeignKey(
        "claim.Claim",
        models.DO_NOTHING,
        db_column="ClaimID",
        related_name="hospital_payment_batch_claims",
    )

    claim_code = models.CharField(db_column="ClaimCode", max_length=50)
    amount = models.DecimalField(
        db_column="Amount", max_digits=18, decimal_places=2
    )

    status = models.SmallIntegerField(
        db_column="Status", default=STATUS_PENDING, choices=STATUS_CHOICES
    )

    payment_reference = models.CharField(
        db_column="PaymentReference", max_length=100, blank=True, null=True
    )
    failure_reason = models.TextField(
        db_column="FailureReason", blank=True, null=True
    )

    audit_user_id = models.IntegerField(db_column="AuditUserID")

    class Meta:
        managed = True
        db_table = "tblHospitalPaymentBatchClaim"
        unique_together = ("payment_batch", "claim")


class HospitalPaymentRecord(core_models.VersionedModel):
    """
    Records the actual payment response received from the external payment API.
    One record per payment API response (a batch may have multiple records
    if partial payments or retries occur).
    """

    id = models.BigAutoField(db_column="HospitalPaymentRecordID", primary_key=True)
    uuid = models.CharField(
        db_column="HospitalPaymentRecordUUID",
        max_length=36,
        default=uuid.uuid4,
        unique=True,
    )

    payment_batch = models.ForeignKey(
        HospitalPaymentBatch,
        models.DO_NOTHING,
        db_column="HospitalPaymentBatchID",
        related_name="payment_records",
    )

    payment_api_reference = models.CharField(
        db_column="PaymentApiReference", max_length=100, blank=True, null=True
    )

    total_paid_amount = models.DecimalField(
        db_column="TotalPaidAmount", max_digits=18, decimal_places=2, default=0
    )

    claims_paid_count = models.IntegerField(
        db_column="ClaimsPaidCount", default=0
    )
    claims_failed_count = models.IntegerField(
        db_column="ClaimsFailedCount", default=0
    )

    status = models.CharField(
        db_column="Status", max_length=20, default="RECEIVED"
    )

    raw_response = models.JSONField(
        db_column="RawResponse", blank=True, null=True
    )

    received_date = fields.DateTimeField(db_column="ReceivedDate")

    audit_user_id = models.IntegerField(db_column="AuditUserID")

    class Meta:
        managed = True
        db_table = "tblHospitalPaymentRecord"

    def __str__(self):
        return (
            f"PaymentRecord {self.uuid} - Batch:{self.payment_batch_id} "
            f"Paid:{self.total_paid_amount}"
        )


class HospitalPaymentMutation(core_models.UUIDModel, core_models.ObjectMutation):
    payment_batch = models.ForeignKey(
        HospitalPaymentBatch,
        models.DO_NOTHING,
        related_name="mutations",
    )
    mutation = models.ForeignKey(
        core_models.MutationLog,
        models.DO_NOTHING,
        related_name="hospital_payment_batches",
    )

    class Meta:
        managed = True
        db_table = "hospital_payment_PaymentBatchMutation"
