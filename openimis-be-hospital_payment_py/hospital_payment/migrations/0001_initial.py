import uuid
from datetime import datetime

from django.db import migrations, models

import core.fields
import core.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("claim", "0016_update_django_scheme_with_missing_fields"),
        ("location", "0013_auto_20230317_1534"),
        ("core", "0019_extended_field"),
    ]

    operations = [
        migrations.CreateModel(
            name="HospitalPaymentBatch",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        db_column="HospitalPaymentBatchID",
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "uuid",
                    models.CharField(
                        db_column="HospitalPaymentBatchUUID",
                        default=uuid.uuid4,
                        max_length=36,
                        unique=True,
                    ),
                ),
                (
                    "validity_from",
                    core.fields.DateTimeField(
                        db_column="ValidityFrom",
                        default=datetime.now,
                    ),
                ),
                (
                    "validity_to",
                    core.fields.DateTimeField(
                        db_column="ValidityTo", blank=True, null=True
                    ),
                ),
                (
                    "legacy_id",
                    models.IntegerField(
                        db_column="LegacyID", blank=True, null=True
                    ),
                ),
                (
                    "batch_code",
                    models.CharField(
                        db_column="BatchCode", max_length=50, unique=True
                    ),
                ),
                (
                    "total_amount",
                    models.DecimalField(
                        db_column="TotalAmount",
                        decimal_places=2,
                        max_digits=18,
                        default=0,
                    ),
                ),
                (
                    "total_claims",
                    models.IntegerField(db_column="TotalClaims", default=0),
                ),
                (
                    "status",
                    models.SmallIntegerField(
                        choices=[
                            (1, "Pending Approval"),
                            (2, "Approved"),
                            (3, "Processing"),
                            (4, "Paid"),
                            (5, "Partially Paid"),
                            (6, "Failed"),
                            (7, "Rejected"),
                        ],
                        db_column="Status",
                        default=1,
                    ),
                ),
                (
                    "approved_date",
                    core.fields.DateTimeField(
                        db_column="ApprovedDate", blank=True, null=True
                    ),
                ),
                (
                    "paid_date",
                    core.fields.DateTimeField(
                        db_column="PaidDate", blank=True, null=True
                    ),
                ),
                (
                    "payment_api_reference",
                    models.CharField(
                        db_column="PaymentApiReference",
                        max_length=100,
                        blank=True,
                        null=True,
                    ),
                ),
                (
                    "payment_api_response",
                    models.JSONField(
                        db_column="PaymentApiResponse", blank=True, null=True
                    ),
                ),
                (
                    "failure_reason",
                    models.TextField(
                        db_column="FailureReason", blank=True, null=True
                    ),
                ),
                (
                    "audit_user_id",
                    models.IntegerField(db_column="AuditUserID"),
                ),
                (
                    "health_facility",
                    models.ForeignKey(
                        db_column="HFID",
                        on_delete=models.DO_NOTHING,
                        related_name="hospital_payment_batches",
                        to="location.healthfacility",
                    ),
                ),
                (
                    "approved_by",
                    models.ForeignKey(
                        blank=True,
                        db_column="ApprovedBy",
                        null=True,
                        on_delete=models.DO_NOTHING,
                        related_name="approved_hospital_payment_batches",
                        to="core.interactiveuser",
                    ),
                ),
            ],
            options={
                "db_table": "tblHospitalPaymentBatch",
                "managed": True,
            },
        ),
        migrations.CreateModel(
            name="HospitalPaymentBatchClaim",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        db_column="HospitalPaymentBatchClaimID",
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "uuid",
                    models.CharField(
                        db_column="HospitalPaymentBatchClaimUUID",
                        default=uuid.uuid4,
                        max_length=36,
                        unique=True,
                    ),
                ),
                (
                    "validity_from",
                    core.fields.DateTimeField(
                        db_column="ValidityFrom",
                        default=datetime.now,
                    ),
                ),
                (
                    "validity_to",
                    core.fields.DateTimeField(
                        db_column="ValidityTo", blank=True, null=True
                    ),
                ),
                (
                    "legacy_id",
                    models.IntegerField(
                        db_column="LegacyID", blank=True, null=True
                    ),
                ),
                (
                    "claim_code",
                    models.CharField(db_column="ClaimCode", max_length=50),
                ),
                (
                    "amount",
                    models.DecimalField(
                        db_column="Amount", decimal_places=2, max_digits=18
                    ),
                ),
                (
                    "status",
                    models.SmallIntegerField(
                        choices=[
                            (1, "Pending"),
                            (2, "Paid"),
                            (3, "Failed"),
                            (4, "Excluded"),
                        ],
                        db_column="Status",
                        default=1,
                    ),
                ),
                (
                    "payment_reference",
                    models.CharField(
                        db_column="PaymentReference",
                        max_length=100,
                        blank=True,
                        null=True,
                    ),
                ),
                (
                    "failure_reason",
                    models.TextField(
                        db_column="FailureReason", blank=True, null=True
                    ),
                ),
                (
                    "audit_user_id",
                    models.IntegerField(db_column="AuditUserID"),
                ),
                (
                    "payment_batch",
                    models.ForeignKey(
                        db_column="HospitalPaymentBatchID",
                        on_delete=models.DO_NOTHING,
                        related_name="batch_claims",
                        to="hospital_payment.hospitalpaymentbatch",
                    ),
                ),
                (
                    "claim",
                    models.ForeignKey(
                        db_column="ClaimID",
                        on_delete=models.DO_NOTHING,
                        related_name="hospital_payment_batch_claims",
                        to="claim.claim",
                    ),
                ),
            ],
            options={
                "db_table": "tblHospitalPaymentBatchClaim",
                "managed": True,
                "unique_together": {("payment_batch", "claim")},
            },
        ),
        migrations.CreateModel(
            name="HospitalPaymentRecord",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        db_column="HospitalPaymentRecordID",
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "uuid",
                    models.CharField(
                        db_column="HospitalPaymentRecordUUID",
                        default=uuid.uuid4,
                        max_length=36,
                        unique=True,
                    ),
                ),
                (
                    "validity_from",
                    core.fields.DateTimeField(
                        db_column="ValidityFrom",
                        default=datetime.now,
                    ),
                ),
                (
                    "validity_to",
                    core.fields.DateTimeField(
                        db_column="ValidityTo", blank=True, null=True
                    ),
                ),
                (
                    "legacy_id",
                    models.IntegerField(
                        db_column="LegacyID", blank=True, null=True
                    ),
                ),
                (
                    "payment_api_reference",
                    models.CharField(
                        db_column="PaymentApiReference",
                        max_length=100,
                        blank=True,
                        null=True,
                    ),
                ),
                (
                    "total_paid_amount",
                    models.DecimalField(
                        db_column="TotalPaidAmount",
                        decimal_places=2,
                        max_digits=18,
                        default=0,
                    ),
                ),
                (
                    "claims_paid_count",
                    models.IntegerField(
                        db_column="ClaimsPaidCount", default=0
                    ),
                ),
                (
                    "claims_failed_count",
                    models.IntegerField(
                        db_column="ClaimsFailedCount", default=0
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        db_column="Status", default="RECEIVED", max_length=20
                    ),
                ),
                (
                    "raw_response",
                    models.JSONField(
                        db_column="RawResponse", blank=True, null=True
                    ),
                ),
                (
                    "received_date",
                    core.fields.DateTimeField(db_column="ReceivedDate"),
                ),
                (
                    "audit_user_id",
                    models.IntegerField(db_column="AuditUserID"),
                ),
                (
                    "payment_batch",
                    models.ForeignKey(
                        db_column="HospitalPaymentBatchID",
                        on_delete=models.DO_NOTHING,
                        related_name="payment_records",
                        to="hospital_payment.hospitalpaymentbatch",
                    ),
                ),
            ],
            options={
                "db_table": "tblHospitalPaymentRecord",
                "managed": True,
            },
        ),
        migrations.CreateModel(
            name="HospitalPaymentMutation",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "payment_batch",
                    models.ForeignKey(
                        on_delete=models.DO_NOTHING,
                        related_name="mutations",
                        to="hospital_payment.hospitalpaymentbatch",
                    ),
                ),
                (
                    "mutation",
                    models.ForeignKey(
                        on_delete=models.DO_NOTHING,
                        related_name="hospital_payment_batches",
                        to="core.mutationlog",
                    ),
                ),
            ],
            options={
                "db_table": "hospital_payment_PaymentBatchMutation",
                "managed": True,
            },
            bases=(models.Model, core.models.ObjectMutation),
        ),
    ]
