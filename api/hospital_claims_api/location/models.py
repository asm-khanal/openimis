from django.db import models


class Location(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="children"
    )
    type = models.CharField(max_length=20, blank=True, default="")
    male_population = models.IntegerField(default=0)
    female_population = models.IntegerField(default=0)

    class Meta:
        db_table = "location_location"

    def __str__(self):
        return f"{self.name} ({self.code})"


class HealthFacilityLegalForm(models.Model):
    code = models.CharField(max_length=10, unique=True)
    legal_form = models.CharField(max_length=100)
    sort_order = models.IntegerField(default=0)

    class Meta:
        db_table = "location_health_facility_legal_form"

    def __str__(self):
        return self.legal_form


class HealthFacilitySubLevel(models.Model):
    code = models.CharField(max_length=10, unique=True)
    health_facility_sub_level = models.CharField(max_length=100)
    sort_order = models.IntegerField(default=0)

    class Meta:
        db_table = "location_health_facility_sub_level"

    def __str__(self):
        return self.health_facility_sub_level


class HealthFacility(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    legal_form = models.ForeignKey(
        HealthFacilityLegalForm, on_delete=models.SET_NULL, null=True, blank=True
    )
    level = models.CharField(max_length=20, blank=True, default="")
    sub_level = models.ForeignKey(
        HealthFacilitySubLevel, on_delete=models.SET_NULL, null=True, blank=True
    )
    location = models.ForeignKey(
        Location, on_delete=models.CASCADE, null=True, blank=True, related_name="health_facilities"
    )
    address = models.CharField(max_length=200, blank=True, default="")
    acc_code = models.CharField(max_length=50, blank=True, default="")
    phone = models.CharField(max_length=50, blank=True, default="")
    email = models.EmailField(blank=True, default="")
    care_type = models.CharField(max_length=20, blank=True, default="")

    class Meta:
        db_table = "location_health_facility"

    def __str__(self):
        return f"{self.name} ({self.code})"
