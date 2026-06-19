from django.db import models
from decimal import Decimal


class Product(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    location = models.ForeignKey(
        "location.Location", on_delete=models.SET_NULL, null=True, blank=True
    )
    insurance_period = models.IntegerField(default=12)
    administration_period = models.IntegerField(default=1)
    lump_sum = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal("0"))
    max_members = models.IntegerField(default=10)
    premium_adult = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal("0"))
    premium_child = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal("0"))
    date_from = models.DateField(null=True, blank=True)
    date_to = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "product_product"

    def __str__(self):
        return f"{self.code} - {self.name}"
