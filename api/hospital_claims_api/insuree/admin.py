from django.contrib import admin
from .models import Gender, FamilyType, Relation, Family, Insuree, InsureePolicy


@admin.register(Gender)
class GenderAdmin(admin.ModelAdmin):
    list_display = ["code", "gender"]


@admin.register(FamilyType)
class FamilyTypeAdmin(admin.ModelAdmin):
    list_display = ["code", "type"]


@admin.register(Relation)
class RelationAdmin(admin.ModelAdmin):
    list_display = ["id", "relation"]


@admin.register(Family)
class FamilyAdmin(admin.ModelAdmin):
    list_display = ["id", "head_insuree", "location"]


@admin.register(Insuree)
class InsureeAdmin(admin.ModelAdmin):
    list_display = ["chf_id", "other_names", "last_name", "gender", "dob", "family"]
    search_fields = ["chf_id", "other_names", "last_name"]


@admin.register(InsureePolicy)
class InsureePolicyAdmin(admin.ModelAdmin):
    list_display = ["insuree", "policy", "enrollment_date"]
