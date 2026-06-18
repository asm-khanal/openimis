from django.contrib import admin

from .models import (
    HospitalPaymentBatch,
    HospitalPaymentBatchClaim,
    HospitalPaymentRecord,
    HospitalPaymentMutation,
)


@admin.register(HospitalPaymentBatch)
class HospitalPaymentBatchAdmin(admin.ModelAdmin):
    list_display = (
        "batch_code",
        "health_facility",
        "total_amount",
        "total_claims",
        "status",
        "approved_date",
        "paid_date",
    )
    list_filter = ("status",)
    search_fields = ("batch_code", "health_facility__code", "health_facility__name")
    readonly_fields = (
        "uuid",
        "batch_code",
        "total_amount",
        "total_claims",
        "payment_api_reference",
        "payment_api_response",
    )
    raw_id_fields = ("health_facility", "approved_by")


@admin.register(HospitalPaymentBatchClaim)
class HospitalPaymentBatchClaimAdmin(admin.ModelAdmin):
    list_display = ("payment_batch", "claim", "claim_code", "amount", "status")
    list_filter = ("status",)
    search_fields = ("claim_code", "payment_batch__batch_code")
    raw_id_fields = ("payment_batch", "claim")


@admin.register(HospitalPaymentRecord)
class HospitalPaymentRecordAdmin(admin.ModelAdmin):
    list_display = (
        "uuid",
        "payment_batch",
        "total_paid_amount",
        "claims_paid_count",
        "claims_failed_count",
        "status",
        "received_date",
    )
    list_filter = ("status",)
    readonly_fields = ("uuid",)
    raw_id_fields = ("payment_batch",)


admin.site.register(HospitalPaymentMutation)
