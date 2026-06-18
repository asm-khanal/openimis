"""
Management command to seed the database with demo data for hackathon.
Loads reference data from CSV files and generates families/insurees/policies.
"""
import csv
import os
import random
import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from location.models import Location, HealthFacility, HealthFacilityLegalForm, HealthFacilitySubLevel
from insuree.models import Gender, FamilyType, Family, Insuree, Relation, InsureePolicy
from medical.models import Diagnosis, Item, Service
from product.models import Product
from policy.models import Policy

SEED_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))), "seed_data")

# If running inside Docker, the seed_data dir is at /openimis-be/seed_data
if not os.path.exists(SEED_DIR):
    SEED_DIR = "/openimis-be/seed_data"

NEPALI_FIRST_NAMES_M = ["Ram", "Krishna", "Hari", "Shiva", "Bishnu", "Ganesh", "Suresh", "Dipak", "Rajesh", "Bikash",
                        "Anil", "Suman", "Nabin", "Prakash", "Ramesh", "Binod", "Kamal", "Hemant", "Dinesh", "Manoj",
                        "Santosh", "Rabin", "Arjun", "Deepak", "Niraj", "Raju", "Sanjay", "Bishal", "Gopal", "Narayan"]
NEPALI_FIRST_NAMES_F = ["Sita", "Gita", "Rita", "Sita", "Kamala", "Radha", "Parbati", "Laxmi", "Saraswati", "Anjali",
                        "Rekha", "Shova", "Nirmala", "Manju", "Bina", "Sarita", "Gauri", "Maya", "Sushma", "Nisha",
                        "Pooja", "Rojina", "Sabita", "Ranjana", "Kalpana", "Dipshikha", "Pratima", "Bandana", "Aastha", "Bishnu"]
NEPALI_LAST_NAMES = ["Sharma", "Poudel", "Adhikari", "Karki", "Thapa", "Gurung", "Magar", "Shrestha", "Maharjan",
                     "Rai", "Limbu", "Tamang", "Newar", "Bhandari", "Acharya", "Pandey", "Upadhyay", "Regmi",
                     "Khadka", "Basnet", "Bista", "Rana", "Joshi", "Devkota", "Koirala", "Nepal", "Dahal", "Khanal",
                     "Oli", "Bhusal"]


def read_csv(filename):
    """Read a CSV file from the seed_data directory."""
    filepath = os.path.join(SEED_DIR, filename)
    if not os.path.exists(filepath):
        return None
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def now():
    return timezone.now()


class Command(BaseCommand):
    help = "Seed the database with demo data from CSV files and generated records"

    def add_arguments(self, parser):
        parser.add_argument(
            "--families", type=int, default=50,
            help="Number of families to generate (default: 50)"
        )
        parser.add_argument(
            "--clean", action="store_true",
            help="Delete existing seed data before loading"
        )

    def handle(self, *args, **options):
        num_families = options["families"]
        clean = options["clean"]

        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("  openIMIS Hospital Payment - Seed Data Loader"))
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
        self._generate_families_and_insurees(num_families)
        self._generate_policies()

        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("  Seed data loaded successfully!"))
        self.stdout.write(self.style.SUCCESS(f"  Families: {num_families}"))
        self.stdout.write(self.style.SUCCESS("=" * 60))

    def _clean_existing_data(self):
        """Delete existing data to allow re-seeding."""
        self.stdout.write("Cleaning existing data...")
        models_to_clean = [
            InsureePolicy, Policy, Insuree, Family,
            HealthFacility, Product, Item, Service, Diagnosis,
            HealthFacilitySubLevel, HealthFacilityLegalForm,
            FamilyType, Gender, Relation, Location,
        ]
        for model in models_to_clean:
            count = model.objects.count()
            if count:
                model.objects.all().delete()
                self.stdout.write(f"  Deleted {count} from {model.__name__}")

    def _load_locations(self):
        """Load locations from CSV."""
        rows = read_csv("locations.csv")
        if not rows:
            self.stdout.write(self.style.WARNING("  locations.csv not found, skipping"))
            return

        self.stdout.write("Loading locations...")
        created = 0
        for row in rows:
            parent = None
            if row.get("parent_code"):
                parent = Location.objects.filter(code=row["parent_code"], validity_to__isnull=True).first()

            obj, created_flag = Location.objects.get_or_create(
                code=row["code"],
                validity_to__isnull=True,
                defaults={
                    "name": row["name"],
                    "type": row["type"],
                    "parent": parent,
                    "male_population": int(row.get("male_population") or 0),
                    "female_population": int(row.get("female_population") or 0),
                    "audit_user_id": -1,
                    "validity_from": now(),
                }
            )
            if created_flag:
                created += 1
        self.stdout.write(f"  Locations: {created} created, {Location.objects.count()} total")

    def _load_reference_data(self):
        """Load genders, family types, legal forms, sub levels, relations."""
        self.stdout.write("Loading reference data...")

        # Genders
        for code, name, sort in [("M", "Male", 1), ("F", "Female", 2), ("O", "Other", 3)]:
            Gender.objects.get_or_create(code=code, defaults={"gender": name, "sort_order": sort})

        # Family types
        for code, name, sort in [("H", "Household", 1), ("I", "Individual", 2)]:
            FamilyType.objects.get_or_create(code=code, defaults={"type": name, "sort_order": sort})

        # Legal forms
        legal_forms = [("G", "Government", 1), ("P", "Private", 2), ("O", "Other", 3)]
        for code, name, sort in legal_forms:
            HealthFacilityLegalForm.objects.get_or_create(code=code, defaults={"legal_form": name, "sort_order": sort})

        # Sub levels
        sub_levels = [("H", "Hospital", 1), ("C", "Health Centre", 2), ("P", "PHC", 3)]
        for code, name, sort in sub_levels:
            HealthFacilitySubLevel.objects.get_or_create(code=code, defaults={"health_facility_sub_level": name, "sort_order": sort})

        # Relations
        relations = [(1, "Head", 1), (2, "Spouse", 2), (3, "Son", 3), (4, "Daughter", 4), (5, "Father", 5), (6, "Mother", 6)]
        for rid, name, sort in relations:
            Relation.objects.get_or_create(id=rid, defaults={"relation": name, "sort_order": sort})

        self.stdout.write(f"  Genders: {Gender.objects.count()}, FamilyTypes: {FamilyType.objects.count()}")
        self.stdout.write(f"  LegalForms: {HealthFacilityLegalForm.objects.count()}, SubLevels: {HealthFacilitySubLevel.objects.count()}")
        self.stdout.write(f"  Relations: {Relation.objects.count()}")

    def _load_diagnoses(self):
        """Load ICD diagnoses from CSV."""
        rows = read_csv("diagnoses.csv")
        if not rows:
            self.stdout.write(self.style.WARNING("  diagnoses.csv not found, skipping"))
            return

        self.stdout.write("Loading diagnoses...")
        created = 0
        for row in rows:
            obj, created_flag = Diagnosis.objects.get_or_create(
                code=row["code"],
                validity_to__isnull=True,
                defaults={
                    "name": row["name"],
                    "audit_user_id": -1,
                    "validity_from": now(),
                }
            )
            if created_flag:
                created += 1
        self.stdout.write(f"  Diagnoses: {created} created, {Diagnosis.objects.count()} total")

    def _load_items(self):
        """Load medical items from CSV."""
        rows = read_csv("items.csv")
        if not rows:
            self.stdout.write(self.style.WARNING("  items.csv not found, skipping"))
            return

        self.stdout.write("Loading items...")
        created = 0
        for row in rows:
            obj, created_flag = Item.objects.get_or_create(
                code=row["code"],
                validity_to__isnull=True,
                defaults={
                    "name": row["name"],
                    "type": row["type"],
                    "package": row.get("package", ""),
                    "price": Decimal(row["price"]),
                    "care_type": row["care_type"],
                    "frequency": int(row.get("frequency") or 1),
                    "patient_category": int(row.get("patient_category") or 15),
                    "audit_user_id": -1,
                    "validity_from": now(),
                }
            )
            if created_flag:
                created += 1
        self.stdout.write(f"  Items: {created} created, {Item.objects.count()} total")

    def _load_services(self):
        """Load medical services from CSV."""
        rows = read_csv("services.csv")
        if not rows:
            self.stdout.write(self.style.WARNING("  services.csv not found, skipping"))
            return

        self.stdout.write("Loading services...")
        created = 0
        for row in rows:
            obj, created_flag = Service.objects.get_or_create(
                code=row["code"],
                validity_to__isnull=True,
                defaults={
                    "name": row["name"],
                    "type": row["type"],
                    "level": row["level"],
                    "price": Decimal(row["price"]),
                    "care_type": row["care_type"],
                    "frequency": int(row.get("frequency") or 1),
                    "patient_category": int(row.get("patient_category") or 15),
                    "audit_user_id": -1,
                    "validity_from": now(),
                }
            )
            if created_flag:
                created += 1
        self.stdout.write(f"  Services: {created} created, {Service.objects.count()} total")

    def _load_products(self):
        """Load insurance products from CSV."""
        rows = read_csv("products.csv")
        if not rows:
            self.stdout.write(self.style.WARNING("  products.csv not found, skipping"))
            return

        self.stdout.write("Loading products...")
        created = 0
        for row in rows:
            location = None
            if row.get("location_code"):
                location = Location.objects.filter(code=row["location_code"], validity_to__isnull=True).first()

            obj, created_flag = Product.objects.get_or_create(
                code=row["code"],
                validity_to__isnull=True,
                defaults={
                    "name": row["name"],
                    "location": location,
                    "insurance_period": int(row["insurance_period"]),
                    "administration_period": int(row.get("administration_period") or 1),
                    "lump_sum": Decimal(row["lump_sum"]),
                    "max_members": int(row["max_members"]),
                    "premium_adult": Decimal(row.get("premium_adult") or 0),
                    "premium_child": Decimal(row.get("premium_child") or 0),
                    "ded_insuree": Decimal(row.get("ded_insuree") or 0),
                    "max_insuree": Decimal(row.get("max_insuree") or 0),
                    "ded_op_insuree": Decimal(row.get("ded_op_insuree") or 0),
                    "max_op_insuree": Decimal(row.get("max_op_insuree") or 0),
                    "ded_ip_insuree": Decimal(row.get("ded_ip_insuree") or 0),
                    "max_ip_insuree": Decimal(row.get("max_ip_insuree") or 0),
                    "grace_period_enrolment": int(row.get("grace_period_enrolment") or 0),
                    "start_cycle_1": row.get("start_cycle_1", "01-01"),
                    "start_cycle_2": row.get("start_cycle_2", "01-07"),
                    "registration_fee": Decimal(row.get("registration_fee") or 0),
                    "general_assembly_fee": Decimal(row.get("general_assembly_fee") or 0),
                    "max_no_consultation": int(row.get("max_no_consultation") or 10),
                    "max_no_surgery": int(row.get("max_no_surgery") or 2),
                    "max_no_delivery": int(row.get("max_no_delivery") or 2),
                    "max_no_hospitalization": int(row.get("max_no_hospitalization") or 3),
                    "max_no_visits": int(row.get("max_no_visits") or 20),
                    "max_no_antenatal": int(row.get("max_no_antenatal") or 8),
                    "date_from": now(),
                    "date_to": now() + timedelta(days=3650),
                    "audit_user_id": -1,
                    "validity_from": now(),
                }
            )
            if created_flag:
                created += 1
        self.stdout.write(f"  Products: {created} created, {Product.objects.count()} total")

    def _load_health_facilities(self):
        """Load health facilities from CSV."""
        rows = read_csv("health_facilities.csv")
        if not rows:
            self.stdout.write(self.style.WARNING("  health_facilities.csv not found, skipping"))
            return

        self.stdout.write("Loading health facilities...")
        created = 0
        for row in rows:
            location = Location.objects.filter(code=row["location_code"], validity_to__isnull=True).first()
            legal_form = HealthFacilityLegalForm.objects.filter(code=row["legal_form"]).first()
            sub_level = HealthFacilitySubLevel.objects.filter(code=row["sub_level"]).first()

            obj, created_flag = HealthFacility.objects.get_or_create(
                code=row["code"],
                validity_to__isnull=True,
                defaults={
                    "name": row["name"],
                    "acc_code": row.get("acc_code", ""),
                    "legal_form": legal_form,
                    "level": row["level"],
                    "sub_level": sub_level,
                    "location": location,
                    "address": row.get("address", ""),
                    "phone": row.get("phone", ""),
                    "email": row.get("email", ""),
                    "care_type": row["care_type"],
                    "audit_user_id": -1,
                    "validity_from": now(),
                }
            )
            if created_flag:
                created += 1
        self.stdout.write(f"  Health Facilities: {created} created, {HealthFacility.objects.count()} total")

    def _generate_families_and_insurees(self, num_families):
        """Generate families with insurees (head + spouse + children)."""
        self.stdout.write(f"Generating {num_families} families with insurees...")

        locations = list(Location.objects.filter(type="M", validity_to__isnull=True))
        if not locations:
            locations = list(Location.objects.filter(validity_to__isnull=True))

        family_types = list(FamilyType.objects.all())
        genders = list(Gender.objects.all())
        relations = list(Relation.objects.all())

        head_relation = Relation.objects.filter(id=1).first()
        spouse_relation = Relation.objects.filter(id=2).first()
        son_relation = Relation.objects.filter(id=3).first()
        daughter_relation = Relation.objects.filter(id=4).first()

        families_created = 0
        insurees_created = 0

        for i in range(num_families):
            location = random.choice(locations)
            family_type = random.choice(family_types)
            last_name = random.choice(NEPALI_LAST_NAMES)

            # Generate head insuree
            is_male = random.random() > 0.5
            first_name = random.choice(NEPALI_FIRST_NAMES_M if is_male else NEPALI_FIRST_NAMES_F)
            head_gender = Gender.objects.get(code="M" if is_male else "F")
            head_dob = date(random.randint(1965, 1995), random.randint(1, 12), random.randint(1, 28))
            chf_id = f"1000{i + 1:06d}"

            head_insuree = Insuree.objects.create(
                chf_id=chf_id,
                last_name=last_name,
                other_names=first_name,
                gender=head_gender,
                dob=head_dob,
                head=True,
                marital="M",
                relationship=head_relation,
                phone=f"98{random.randint(10000000, 99999999)}",
                audit_user_id=-1,
                validity_from=now(),
                status="AC",
            )
            insurees_created += 1

            # Create family
            family = Family.objects.create(
                head_insuree=head_insuree,
                location=location,
                family_type=family_type,
                poverty=random.random() > 0.7,
                address=f"{location.name}-{random.randint(1, 20)}",
                audit_user_id=-1,
                validity_from=now(),
            )
            # Link head insuree to family
            head_insuree.family = family
            head_insuree.save()
            families_created += 1

            # Generate spouse
            spouse_gender = Gender.objects.get(code="F" if is_male else "M")
            spouse_name = random.choice(NEPALI_FIRST_NAMES_F if is_male else NEPALI_FIRST_NAMES_M)
            spouse_dob = date(random.randint(1965, 1995), random.randint(1, 12), random.randint(1, 28))
            Insuree.objects.create(
                chf_id=f"1000{i + 1:06d}S",
                last_name=last_name if is_male else random.choice(NEPALI_LAST_NAMES),
                other_names=spouse_name,
                gender=spouse_gender,
                dob=spouse_dob,
                head=False,
                marital="M",
                family=family,
                relationship=spouse_relation,
                audit_user_id=-1,
                validity_from=now(),
                status="AC",
            )
            insurees_created += 1

            # Generate 1-3 children
            num_children = random.randint(1, 3)
            for j in range(num_children):
                child_is_male = random.random() > 0.5
                child_name = random.choice(NEPALI_FIRST_NAMES_M if child_is_male else NEPALI_FIRST_NAMES_F)
                child_gender = Gender.objects.get(code="M" if child_is_male else "F")
                child_dob = date(random.randint(2000, 2020), random.randint(1, 12), random.randint(1, 28))
                child_relation = son_relation if child_is_male else daughter_relation
                Insuree.objects.create(
                    chf_id=f"1000{i + 1:06d}C{j + 1}",
                    last_name=last_name,
                    other_names=child_name,
                    gender=child_gender,
                    dob=child_dob,
                    head=False,
                    family=family,
                    relationship=child_relation,
                    audit_user_id=-1,
                    validity_from=now(),
                    status="AC",
                )
                insurees_created += 1

        self.stdout.write(f"  Families: {families_created}, Insurees: {insurees_created}")

    def _generate_policies(self):
        """Generate active policies for all families."""
        self.stdout.write("Generating policies...")

        products = list(Product.objects.filter(validity_to__isnull=True))
        if not products:
            self.stdout.write(self.style.WARNING("  No products found, skipping policies"))
            return

        families = list(Family.objects.filter(validity_to__isnull=True))
        policies_created = 0
        insuree_policies_created = 0

        enroll_date = date(2025, 1, 15)
        start_date = date(2025, 2, 1)
        effective_date = date(2025, 2, 1)
        expiry_date = date(2026, 1, 31)

        for family in families:
            product = random.choice(products)
            members = list(Insuree.objects.filter(family=family, validity_to__isnull=True))

            policy = Policy.objects.create(
                family=family,
                product=product,
                status=Policy.STATUS_ACTIVE,
                stage=Policy.STAGE_NEW,
                enroll_date=enroll_date,
                start_date=start_date,
                effective_date=effective_date,
                expiry_date=expiry_date,
                value=Decimal("5000.00"),
                audit_user_id=-1,
                validity_from=now(),
            )
            policies_created += 1

            for member in members:
                InsureePolicy.objects.create(
                    insuree=member,
                    policy=policy,
                    enrollment_date=enroll_date,
                    start_date=start_date,
                    effective_date=effective_date,
                    expiry_date=expiry_date,
                    audit_user_id=-1,
                    validity_from=now(),
                )
                insuree_policies_created += 1

        self.stdout.write(f"  Policies: {policies_created}, InsureePolicies: {insuree_policies_created}")
