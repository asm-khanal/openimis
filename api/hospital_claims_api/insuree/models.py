from django.db import models


class Gender(models.Model):
    code = models.CharField(max_length=10, unique=True)
    gender = models.CharField(max_length=50)
    sort_order = models.IntegerField(default=0)

    class Meta:
        db_table = "insuree_gender"

    def __str__(self):
        return self.gender


class FamilyType(models.Model):
    code = models.CharField(max_length=10, unique=True)
    type = models.CharField(max_length=100)
    sort_order = models.IntegerField(default=0)

    class Meta:
        db_table = "insuree_family_type"

    def __str__(self):
        return self.type


class Relation(models.Model):
    id = models.IntegerField(primary_key=True)
    relation = models.CharField(max_length=100)
    sort_order = models.IntegerField(default=0)

    class Meta:
        db_table = "insuree_relation"

    def __str__(self):
        return self.relation


class Family(models.Model):
    head_insuree = models.ForeignKey(
        "Insuree", on_delete=models.CASCADE, null=True, blank=True, related_name="headed_families"
    )
    location = models.ForeignKey(
        "location.Location", on_delete=models.SET_NULL, null=True, blank=True
    )
    family_type = models.ForeignKey(
        FamilyType, on_delete=models.SET_NULL, null=True, blank=True
    )
    poverty = models.BooleanField(default=False)
    address = models.CharField(max_length=200, blank=True, default="")

    class Meta:
        db_table = "insuree_family"

    def __str__(self):
        head = self.head_insuree
        return f"Family #{self.id} - {head}"


class Insuree(models.Model):
    chf_id = models.CharField(max_length=20, unique=True)
    last_name = models.CharField(max_length=100, blank=True, default="")
    other_names = models.CharField(max_length=100, blank=True, default="")
    gender = models.ForeignKey(
        Gender, on_delete=models.SET_NULL, null=True, blank=True
    )
    dob = models.DateField(null=True, blank=True)
    head = models.BooleanField(default=False)
    marital = models.CharField(max_length=10, blank=True, default="")
    relationship = models.ForeignKey(
        Relation, on_delete=models.SET_NULL, null=True, blank=True
    )
    family = models.ForeignKey(
        Family, on_delete=models.CASCADE, null=True, blank=True, related_name="members"
    )
    phone = models.CharField(max_length=50, blank=True, default="")
    email = models.EmailField(blank=True, default="")
    status = models.CharField(max_length=10, blank=True, default="AC")

    class Meta:
        db_table = "insuree_insuree"

    def __str__(self):
        return f"{self.chf_id} - {self.other_names} {self.last_name}"


class InsureePolicy(models.Model):
    insuree = models.ForeignKey(
        Insuree, on_delete=models.CASCADE, related_name="policies"
    )
    policy = models.ForeignKey(
        "policy.Policy", on_delete=models.CASCADE, related_name="insuree_policies"
    )
    enrollment_date = models.DateField(null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    effective_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "insuree_insuree_policy"
        unique_together = [("insuree", "policy")]

    def __str__(self):
        return f"{self.insuree.chf_id} -> {self.policy}"
