import csv
import os
import random
from datetime import date, timedelta
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from location.models import Location, HealthFacility, HealthFacilityLegalForm, HealthFacilitySubLevel
from insuree.models import Gender, FamilyType, Relation, Family, Insuree, InsureePolicy
from medical.models import Diagnosis, Item, Service
from product.models import Product
from policy.models import Policy

SEED_DIR = os.path.join(settings.BASE_DIR, "seed_data")

NEPALI_FIRST_M = ["Ram", "Krishna", "Hari", "Shiva", "Bishnu", "Ganesh", "Suresh", "Dipak", "Rajesh", "Bikash",
                   "Anil", "Suman", "Nabin", "Prakash", "Ramesh", "Binod", "Kamal", "Hemant", "Dinesh", "Manoj",
                   "Santosh", "Rabin", "Arjun", "Deepak", "Niraj", "Raju", "Sanjay", "Bishal", "Gopal", "Narayan"]
NEPALI_FIRST_F = ["Sita", "Gita", "Rita", "Kamala", "Radha", "Parbati", "Laxmi", "Saraswati", "Anjali",
                   "Rekha", "Shova", "Nirmala", "Manju", "Bina", "Sarita", "Gauri", "Maya", "Sushma", "Nisha",
                   "Pooja", "Rojina", "Sabita", "Ranjana", "Kalpana", "Dipshikha", "Pratima", "Bandana", "Aastha"]
NEPALI_LAST = ["Sharma", "Poudel", "Adhikari", "Karki", "Thapa", "Gurung", "Magar", "Shrestha", "Maharjan",
                "Rai", "Limbu", "Tamang", "Newar", "Bhandari", "Acharya", "Pandey", "Upadhyay", "Regmi",
                "Khadka", "Basnet", "Bista", "Rana", "Joshi", "Devkota", "Koirala", "Nepal", "Dahal", "Khanal",
                "Oli", "Bhusal"]


def read_csv(filename):
    filepath = os.path.join(SEED_DIR, filename)
    if not os.path.exists(filepath):
        return None
    with open(filepath, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


class Command(BaseCommand):
    help = "Load seed data from CSV files and generate demo records"

    def add_arguments(self, parser):
        parser.add_argument("--families", type=int, default=50, help="Number of families to generate (default: 50)")
        parser.add_argument("--clean", action="store_true", help="Delete existing seed data before loading")

    def handle(self, *args, **options):
        num_families = options["families"]
        clean = options["clean"]

        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("  Hospital Claims API - Seed Data Loader"))
        self.stdout.write(self.style.SUCCESS("=" * 60))

        if clean:
            self._clean_existing_data()

        self._load_locations()
        self._load_reference_data()
        self._load_diagnoses()
        self._load_items()
        self._load_services()
        self._load_products()
        self._load_health_facilities()
        self._load_users()
        self._generate_families_and_insurees(num_families)
        self._generate_policies()

        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("  Seed data loaded successfully!"))
        self.stdout.write(self.style.SUCCESS(f"  Families: {num_families}"))
        self.stdout.write(self.style.SUCCESS("=" * 60))

    def _clean_existing_data(self):
        self.stdout.write("Cleaning existing data...")
        models = [InsureePolicy, Policy, Insuree, Family, HealthFacility, Product, Item, Service, Diagnosis,
                  HealthFacilitySubLevel, HealthFacilityLegalForm, FamilyType, Gender, Relation, Location]
        for m in models:
            count = m.objects.count()
            if count:
                m.objects.all().delete()
                self.stdout.write(f"  Deleted {count} from {m.__name__}")

    def _load_locations(self):
        rows = read_csv("locations.csv")
        if not rows:
            self.stdout.write(self.style.WARNING("  locations.csv not found, skipping"))
            return
        self.stdout.write("Loading locations...")
        created = 0
        for row in rows:
            parent = None
            if row.get("parent_code"):
                parent = Location.objects.filter(code=row["parent_code"]).first()
            obj, flag = Location.objects.get_or_create(
                code=row["code"],
                defaults={
                    "name": row["name"],
                    "type": row["type"],
                    "parent": parent,
                    "male_population": int(row.get("male_population") or 0),
                    "female_population": int(row.get("female_population") or 0),
                }
            )
            if flag:
                created += 1
        self.stdout.write(f"  Locations: {created} created, {Location.objects.count()} total")

    def _load_reference_data(self):
        self.stdout.write("Loading reference data...")
        for code, name, sort in [("M", "Male", 1), ("F", "Female", 2), ("O", "Other", 3)]:
            Gender.objects.get_or_create(code=code, defaults={"gender": name, "sort_order": sort})
        for code, name, sort in [("H", "Household", 1), ("I", "Individual", 2)]:
            FamilyType.objects.get_or_create(code=code, defaults={"type": name, "sort_order": sort})
        for code, name, sort in [("G", "Government", 1), ("P", "Private", 2), ("O", "Other", 3)]:
            HealthFacilityLegalForm.objects.get_or_create(code=code, defaults={"legal_form": name, "sort_order": sort})
        for code, name, sort in [("H", "Hospital", 1), ("C", "Health Centre", 2), ("P", "PHC", 3)]:
            HealthFacilitySubLevel.objects.get_or_create(code=code, defaults={"health_facility_sub_level": name, "sort_order": sort})
        for rid, name, sort in [(1, "Head", 1), (2, "Spouse", 2), (3, "Son", 3), (4, "Daughter", 4), (5, "Father", 5), (6, "Mother", 6)]:
            Relation.objects.get_or_create(id=rid, defaults={"relation": name, "sort_order": sort})
        self.stdout.write(f"  Genders: {Gender.objects.count()}, FamilyTypes: {FamilyType.objects.count()}")
        self.stdout.write(f"  LegalForms: {HealthFacilityLegalForm.objects.count()}, SubLevels: {HealthFacilitySubLevel.objects.count()}")
        self.stdout.write(f"  Relations: {Relation.objects.count()}")

    def _load_diagnoses(self):
        rows = read_csv("diagnoses.csv")
        if not rows:
            self.stdout.write(self.style.WARNING("  diagnoses.csv not found, skipping"))
            return
        self.stdout.write("Loading diagnoses...")
        created = 0
        for row in rows:
            obj, flag = Diagnosis.objects.get_or_create(code=row["code"], defaults={"name": row["name"]})
            if flag:
                created += 1
        self.stdout.write(f"  Diagnoses: {created} created, {Diagnosis.objects.count()} total")

    def _load_items(self):
        rows = read_csv("items.csv")
        if not rows:
            self.stdout.write(self.style.WARNING("  items.csv not found, skipping"))
            return
        self.stdout.write("Loading items...")
        created = 0
        for row in rows:
            obj, flag = Item.objects.get_or_create(
                code=row["code"],
                defaults={
                    "name": row["name"], "type": row["type"], "package": row.get("package", ""),
                    "price": Decimal(row["price"]), "care_type": row["care_type"],
                    "frequency": int(row.get("frequency") or 1), "patient_category": int(row.get("patient_category") or 15),
                }
            )
            if flag:
                created += 1
        self.stdout.write(f"  Items: {created} created, {Item.objects.count()} total")

    def _load_services(self):
        rows = read_csv("services.csv")
        if not rows:
            self.stdout.write(self.style.WARNING("  services.csv not found, skipping"))
            return
        self.stdout.write("Loading services...")
        created = 0
        for row in rows:
            obj, flag = Service.objects.get_or_create(
                code=row["code"],
                defaults={
                    "name": row["name"], "type": row["type"], "level": row["level"],
                    "price": Decimal(row["price"]), "care_type": row["care_type"],
                    "frequency": int(row.get("frequency") or 1), "patient_category": int(row.get("patient_category") or 15),
                }
            )
            if flag:
                created += 1
        self.stdout.write(f"  Services: {created} created, {Service.objects.count()} total")

    def _load_products(self):
        rows = read_csv("products.csv")
        if not rows:
            self.stdout.write(self.style.WARNING("  products.csv not found, skipping"))
            return
        self.stdout.write("Loading products...")
        created = 0
        for row in rows:
            location = None
            if row.get("location_code"):
                location = Location.objects.filter(code=row["location_code"]).first()
            obj, flag = Product.objects.get_or_create(
                code=row["code"],
                defaults={
                    "name": row["name"], "location": location,
                    "insurance_period": int(row["insurance_period"]),
                    "administration_period": int(row.get("administration_period") or 1),
                    "lump_sum": Decimal(row["lump_sum"]), "max_members": int(row["max_members"]),
                    "premium_adult": Decimal(row.get("premium_adult") or 0),
                    "premium_child": Decimal(row.get("premium_child") or 0),
                    "date_from": timezone.now(),
                    "date_to": timezone.now() + timedelta(days=3650),
                }
            )
            if flag:
                created += 1
        self.stdout.write(f"  Products: {created} created, {Product.objects.count()} total")

    def _load_health_facilities(self):
        rows = read_csv("health_facilities.csv")
        if not rows:
            self.stdout.write(self.style.WARNING("  health_facilities.csv not found, skipping"))
            return
        self.stdout.write("Loading health facilities...")
        created = 0
        for row in rows:
            location = Location.objects.filter(code=row["location_code"]).first()
            legal_form = HealthFacilityLegalForm.objects.filter(code=row["legal_form"]).first()
            sub_level = HealthFacilitySubLevel.objects.filter(code=row["sub_level"]).first()
            obj, flag = HealthFacility.objects.get_or_create(
                code=row["code"],
                defaults={
                    "name": row["name"], "acc_code": row.get("acc_code", ""),
                    "legal_form": legal_form, "level": row["level"], "sub_level": sub_level,
                    "location": location, "address": row.get("address", ""),
                    "phone": row.get("phone", ""), "email": row.get("email", ""),
                    "care_type": row["care_type"],
                }
            )
            if flag:
                created += 1
        self.stdout.write(f"  Health Facilities: {created} created, {HealthFacility.objects.count()} total")

    def _load_users(self):
        from django.contrib.auth.models import User
        rows = read_csv("users.csv")
        if not rows:
            self.stdout.write(self.style.WARNING("  users.csv not found, skipping user creation"))
            return
        self.stdout.write("Loading users from CSV...")
        created = 0
        for row in rows:
            username = row["username"]
            password = row["password"]
            role = row.get("role", "staff")
            hf_code = row.get("health_facility_code", "")
            user, flag = User.objects.get_or_create(
                username=username,
                defaults={"is_staff": True},
            )
            if flag:
                user.set_password(password)
                if role == "admin":
                    user.is_superuser = True
                    user.is_staff = True
                user.save()
                created += 1
            else:
                if role == "admin":
                    user.is_superuser = True
                    user.is_staff = True
                    user.save()
        self.stdout.write(f"  Users: {created} created, {User.objects.count()} total")

    def _generate_families_and_insurees(self, num_families):
        self.stdout.write(f"Generating {num_families} families with insurees...")
        locations = list(Location.objects.filter(type="M"))
        if not locations:
            locations = list(Location.objects.all())
        genders = list(Gender.objects.all())
        head_rel = Relation.objects.filter(id=1).first()
        spouse_rel = Relation.objects.filter(id=2).first()
        son_rel = Relation.objects.filter(id=3).first()
        daughter_rel = Relation.objects.filter(id=4).first()

        families_created = 0
        insurees_created = 0

        for i in range(num_families):
            location = random.choice(locations)
            last_name = random.choice(NEPALI_LAST)
            is_male = random.random() > 0.5
            first_name = random.choice(NEPALI_FIRST_M if is_male else NEPALI_FIRST_F)
            head_gender = Gender.objects.get(code="M" if is_male else "F")
            head_dob = date(random.randint(1965, 1995), random.randint(1, 12), random.randint(1, 28))
            chf_id = f"1000{i + 1:06d}"

            head = Insuree.objects.create(
                chf_id=chf_id, last_name=last_name, other_names=first_name,
                gender=head_gender, dob=head_dob, head=True, marital="M",
                relationship=head_rel, phone=f"98{random.randint(10000000, 99999999)}",
                status="AC",
            )
            insurees_created += 1

            family = Family.objects.create(
                head_insuree=head, location=location,
                family_type=FamilyType.objects.first(),
                poverty=random.random() > 0.7,
                address=f"{location.name}-{random.randint(1, 20)}",
            )
            head.family = family
            head.save()
            families_created += 1

            spouse_gender = Gender.objects.get(code="F" if is_male else "M")
            spouse_name = random.choice(NEPALI_FIRST_F if is_male else NEPALI_FIRST_M)
            spouse_dob = date(random.randint(1965, 1995), random.randint(1, 12), random.randint(1, 28))
            Insuree.objects.create(
                chf_id=f"1000{i + 1:06d}S", last_name=last_name if is_male else random.choice(NEPALI_LAST),
                other_names=spouse_name, gender=spouse_gender, dob=spouse_dob,
                head=False, marital="M", family=family, relationship=spouse_rel, status="AC",
            )
            insurees_created += 1

            for j in range(random.randint(1, 3)):
                child_male = random.random() > 0.5
                child_name = random.choice(NEPALI_FIRST_M if child_male else NEPALI_FIRST_F)
                child_gender = Gender.objects.get(code="M" if child_male else "F")
                child_dob = date(random.randint(2000, 2020), random.randint(1, 12), random.randint(1, 28))
                Insuree.objects.create(
                    chf_id=f"1000{i + 1:06d}C{j + 1}", last_name=last_name,
                    other_names=child_name, gender=child_gender, dob=child_dob,
                    head=False, family=family, relationship=son_rel if child_male else daughter_rel, status="AC",
                )
                insurees_created += 1

        self.stdout.write(f"  Families: {families_created}, Insurees: {insurees_created}")

    def _generate_policies(self):
        self.stdout.write("Generating policies...")
        products = list(Product.objects.all())
        if not products:
            self.stdout.write(self.style.WARNING("  No products found, skipping policies"))
            return
        families = list(Family.objects.all())
        policies_created = 0
        ip_created = 0
        enroll_date = date(2025, 1, 15)
        start_date = date(2025, 2, 1)
        expiry_date = date(2026, 1, 31)

        for family in families:
            product = random.choice(products)
            members = list(Insuree.objects.filter(family=family))
            policy = Policy.objects.create(
                family=family, product=product, status=Policy.STATUS_ACTIVE, stage=Policy.STAGE_NEW,
                enroll_date=enroll_date, start_date=start_date, effective_date=start_date,
                expiry_date=expiry_date, value=Decimal("5000.00"),
            )
            policies_created += 1
            for member in members:
                InsureePolicy.objects.create(
                    insuree=member, policy=policy, enrollment_date=enroll_date,
                    start_date=start_date, effective_date=start_date, expiry_date=expiry_date,
                )
                ip_created += 1

        self.stdout.write(f"  Policies: {policies_created}, InsureePolicies: {ip_created}")
