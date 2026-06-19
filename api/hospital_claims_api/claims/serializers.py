from rest_framework import serializers
from claim_app.models import Claim, ClaimItem, ClaimService
from hospital_payment.models import HospitalPaymentBatch, HospitalPaymentBatchClaim, HospitalPaymentRecord


class ClaimItemSerializer(serializers.ModelSerializer):
    item_code = serializers.CharField(source="item.code", read_only=True)
    item_name = serializers.CharField(source="item.name", read_only=True)

    class Meta:
        model = ClaimItem
        fields = ["id", "item", "item_code", "item_name", "qty_claimed", "price_claimed", "remunerated_amount"]


class ClaimServiceSerializer(serializers.ModelSerializer):
    service_code = serializers.CharField(source="service.code", read_only=True)
    service_name = serializers.CharField(source="service.name", read_only=True)

    class Meta:
        model = ClaimService
        fields = ["id", "service", "service_code", "service_name", "qty_claimed", "price_claimed", "remunerated_amount"]


class ClaimListSerializer(serializers.ModelSerializer):
    health_facility_code = serializers.CharField(source="health_facility.code", read_only=True)
    health_facility_name = serializers.CharField(source="health_facility.name", read_only=True)
    insuree_name = serializers.SerializerMethodField()
    insuree_chf_id = serializers.CharField(source="insuree.chf_id", read_only=True)
    diagnosis_code = serializers.CharField(source="diagnosis.code", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Claim
        fields = [
            "id", "uuid", "code", "insuree", "insuree_name", "insuree_chf_id",
            "health_facility", "health_facility_code", "health_facility_name",
            "diagnosis", "diagnosis_code", "date_from", "date_to",
            "status", "status_display", "claimed", "remunerated",
            "created_by", "created_at",
        ]

    def get_insuree_name(self, obj):
        if obj.insuree:
            return f"{obj.insuree.other_names} {obj.insuree.last_name}"
        return None


class ClaimDetailSerializer(serializers.ModelSerializer):
    items = ClaimItemSerializer(many=True, read_only=True)
    services = ClaimServiceSerializer(many=True, read_only=True)
    health_facility_code = serializers.CharField(source="health_facility.code", read_only=True)
    health_facility_name = serializers.CharField(source="health_facility.name", read_only=True)
    insuree_name = serializers.SerializerMethodField()
    insuree_chf_id = serializers.CharField(source="insuree.chf_id", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Claim
        fields = [
            "id", "uuid", "code", "insuree", "insuree_name", "insuree_chf_id",
            "health_facility", "health_facility_code", "health_facility_name",
            "diagnosis", "date_from", "date_to",
            "status", "status_display", "claimed", "remunerated",
            "items", "services",
            "created_by", "created_at", "updated_at",
        ]

    def get_insuree_name(self, obj):
        if obj.insuree:
            return f"{obj.insuree.other_names} {obj.insuree.last_name}"
        return None


class ClaimCreateSerializer(serializers.Serializer):
    health_facility_code = serializers.CharField()
    insuree_chf_id = serializers.CharField()
    diagnosis_code = serializers.CharField(required=False, allow_blank=True)
    date_from = serializers.DateField()
    date_to = serializers.DateField(required=False, allow_null=True)
    items = serializers.ListField(required=False, default=list)
    services = serializers.ListField(required=False, default=list)

    class Meta:
        fields = [
            "health_facility_code", "insuree_chf_id", "diagnosis_code",
            "date_from", "date_to", "items", "services",
        ]


class HospitalPaymentBatchClaimSerializer(serializers.ModelSerializer):
    class Meta:
        model = HospitalPaymentBatchClaim
        fields = [
            "id", "uuid", "claim_code", "claim_id", "amount",
            "status", "payment_reference", "failure_reason",
        ]
        read_only_fields = ["id", "uuid", "payment_reference", "failure_reason"]


class HospitalPaymentBatchListSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    batch_claims = HospitalPaymentBatchClaimSerializer(many=True, read_only=True)
    health_facility_code = serializers.CharField(source="health_facility.code", read_only=True)
    health_facility_name = serializers.CharField(source="health_facility.name", read_only=True)

    class Meta:
        model = HospitalPaymentBatch
        fields = [
            "id", "uuid", "batch_code",
            "health_facility", "health_facility_code", "health_facility_name",
            "total_amount", "total_claims",
            "status", "status_display",
            "approved_by", "approved_date", "paid_date",
            "payment_api_reference", "failure_reason",
            "batch_claims", "created_at",
        ]


class ApprovePaymentBatchSerializer(serializers.Serializer):
    batch_ids = serializers.ListField(child=serializers.IntegerField(), min_length=1)


class PaymentWebhookSerializer(serializers.Serializer):
    batch_reference = serializers.CharField(max_length=100)
    payment_reference = serializers.CharField(max_length=100, required=False)
    status = serializers.CharField(max_length=20)
    total_paid_amount = serializers.DecimalField(max_digits=18, decimal_places=2, required=False)
    claims_paid = serializers.ListField(child=serializers.CharField(), required=False)
    claims_failed = serializers.ListField(child=serializers.CharField(), required=False)
    raw_response = serializers.JSONField(required=False)


class HospitalPaymentRecordSerializer(serializers.ModelSerializer):
    payment_batch_code = serializers.CharField(source="payment_batch.batch_code", read_only=True)

    class Meta:
        model = HospitalPaymentRecord
        fields = [
            "id", "uuid", "payment_batch", "payment_batch_code",
            "payment_api_reference", "total_paid_amount",
            "claims_paid_count", "claims_failed_count",
            "status", "raw_response", "received_date",
        ]
        read_only_fields = fields
