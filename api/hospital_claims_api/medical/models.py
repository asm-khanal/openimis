from django.db import models
from decimal import Decimal


class Diagnosis(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)

    class Meta:
        db_table = "medical_diagnosis"
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.name}"


class Item(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    type = models.CharField(max_length=20, blank=True, default="")
    package = models.CharField(max_length=50, blank=True, default="")
    price = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal("0"))
    care_type = models.CharField(max_length=20, blank=True, default="")
    frequency = models.IntegerField(default=1)
    patient_category = models.IntegerField(default=15)

    class Meta:
        db_table = "medical_item"
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.name}"


class Service(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    type = models.CharField(max_length=20, blank=True, default="")
    level = models.CharField(max_length=20, blank=True, default="")
    price = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal("0"))
    care_type = models.CharField(max_length=20, blank=True, default="")
    frequency = models.IntegerField(default=1)
    patient_category = models.IntegerField(default=15)

    class Meta:
        db_table = "medical_service"
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.name}"
