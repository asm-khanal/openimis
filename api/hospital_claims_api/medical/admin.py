from django.contrib import admin
from .models import Diagnosis, Item, Service


@admin.register(Diagnosis)
class DiagnosisAdmin(admin.ModelAdmin):
    list_display = ["code", "name"]


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ["code", "name"]


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ["code", "name"]
