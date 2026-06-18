from rest_framework import serializers
from .models import (
    HospitalPaymentBatch,
    HospitalPaymentBatchClaim,
    HospitalPaymentRecord,
)
from claim.models import Claim


class HospitalPaymentBatchClaimSerializer(serializers.ModelSerializer):
    claim_code = serializers.CharField(source="claim.code", read_only=True)
    claim_uuid = serializers.UUIDField(source="claim.uuid", read_only=True)
    claim_date = serializers.DateField(source="claim.date_from", read_only=True)
    insuree_name = serializers.SerializerMethodField()
    claimed_amount = serializers.DecimalField(
        source="claim.claimed", max_digits=18, decimal_places=2, read_only=True
    )

    class Meta:
        model = HospitalPaymentBatchClaim
        fields = [
            "id",
            "uuid",
            "claim",
            "claim_code",
            "claim_uuid",
            "claim_date",
            "insuree_name",
            "claimed_amount",
            "amount",
            "status",
            "payment_reference",
            "failure_reason",
        ]
        read_only_fields = ["id", "uuid", "payment_reference", "failure_reason"]

    def get_insuree_name(self, obj):
        insuree = obj.claim.insuree
        return f"{insuree.other_names} {insuree.last_name}" if insuree else None


class HospitalPaymentBatchSerializer(serializers.ModelSerializer):
    health_facility_name = serializers.CharField(
        source="health_facility.name", read_only=True
    )
    health_facility_code = serializers.CharField(
        source="health_facility.code", read_only=True
    )
    health_facility_acc_code = serializers.CharField(
        source="health_facility.acc_code", read_only=True
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    batch_claims = HospitalPaymentBatchClaimSerializer(many=True, read_only=True)
    approved_by_name = serializers.SerializerMethodField()

    class Meta:
        model = HospitalPaymentBatch
        fields = [
            "id",
            "uuid",
            "batch_code",
            "health_facility",
            "health_facility_name",
            "health_facility_code",
            "health_facility_acc_code",
            "total_amount",
            "total_claims",
            "status",
            "status_display",
            "approved_by",
            "approved_by_name",
            "approved_date",
            "paid_date",
            "payment_api_reference",
            "payment_api_response",
            "failure_reason",
            "batch_claims",
            "validity_from",
            "validity_to",
        ]
        read_only_fields = [
            "id",
            "uuid",
            "batch_code",
            "total_amount",
            "total_claims",
            "approved_by",
            "approved_date",
            "paid_date",
            "payment_api_reference",
            "payment_api_response",
            "failure_reason",
            "validity_from",
            "validity_to",
        ]

    def get_approved_by_name(self, obj):
        if obj.approved_by:
            return f"{obj.approved_by.other_names} {obj.approved_by.last_name}"
        return None


class HospitalPaymentRecordSerializer(serializers.ModelSerializer):
    payment_batch_code = serializers.CharField(
        source="payment_batch.batch_code", read_only=True
    )

    class Meta:
        model = HospitalPaymentRecord
        fields = [
            "id",
            "uuid",
            "payment_batch",
            "payment_batch_code",
            "payment_api_reference",
            "total_paid_amount",
            "claims_paid_count",
            "claims_failed_count",
            "status",
            "raw_response",
            "received_date",
        ]
        read_only_fields = fields


class ApprovePaymentBatchSerializer(serializers.Serializer):
    """Serializer for the approve payment batch action."""
    batch_ids = serializers.ListField(
        child=serializers.IntegerField(), min_length=1
    )


class PaymentWebhookSerializer(serializers.Serializer):
    """Serializer for receiving payment confirmation from external payment API."""
    batch_reference = serializers.CharField(max_length=100)
    payment_reference = serializers.CharField(max_length=100, required=False)
    status = serializers.CharField(max_length=20)
    total_paid_amount = serializers.DecimalField(
        max_digits=18, decimal_places=2, required=False
    )
    claims_paid = serializers.ListField(
        child=serializers.IntegerField(), required=False
    )
    claims_failed = serializers.ListField(
        child=serializers.IntegerField(), required=False
    )
    raw_response = serializers.JSONField(required=False)
