from django.contrib import admin
from .models import Claim, ClaimItem, ClaimService


@admin.register(Claim)
class ClaimAdmin(admin.ModelAdmin):
    list_display = ["code", "status", "insuree", "health_facility", "claimed", "created_at"]
    list_filter = ["status"]


@admin.register(ClaimItem)
class ClaimItemAdmin(admin.ModelAdmin):
    list_display = ["claim", "item", "qty_claimed", "price_claimed"]


@admin.register(ClaimService)
class ClaimServiceAdmin(admin.ModelAdmin):
    list_display = ["claim", "service", "qty_claimed", "price_claimed"]
