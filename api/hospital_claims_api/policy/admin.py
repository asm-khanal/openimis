from django.contrib import admin
from .models import Policy


@admin.register(Policy)
class PolicyAdmin(admin.ModelAdmin):
    list_display = ["id", "product", "family", "status", "start_date", "expiry_date"]
