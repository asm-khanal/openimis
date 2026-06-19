from django.contrib import admin
from .models import Location, HealthFacility, HealthFacilityLegalForm, HealthFacilitySubLevel


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "parent", "type"]


@admin.register(HealthFacility)
class HealthFacilityAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "location", "acc_code", "care_type"]


@admin.register(HealthFacilityLegalForm)
class HealthFacilityLegalFormAdmin(admin.ModelAdmin):
    list_display = ["code", "legal_form"]


@admin.register(HealthFacilitySubLevel)
class HealthFacilitySubLevelAdmin(admin.ModelAdmin):
    list_display = ["code", "health_facility_sub_level"]
