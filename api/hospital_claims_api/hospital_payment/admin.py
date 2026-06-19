from django.contrib import admin
from .models import HospitalPaymentBatch, HospitalPaymentBatchClaim, HospitalPaymentRecord


@admin.register(HospitalPaymentBatch)
class HospitalPaymentBatchAdmin(admin.ModelAdmin):
    list_display = ["batch_code", "health_facility", "status", "total_amount", "created_at"]
    list_filter = ["status"]


@admin.register(HospitalPaymentBatchClaim)
class HospitalPaymentBatchClaimAdmin(admin.ModelAdmin):
    list_display = ["claim_code", "payment_batch", "amount", "status"]


@admin.register(HospitalPaymentRecord)
class HospitalPaymentRecordAdmin(admin.ModelAdmin):
    list_display = ["payment_batch", "payment_api_reference", "status", "received_date"]
