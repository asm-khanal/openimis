import csv
import os
import logging
from django.conf import settings
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User
from rest_framework import authentication
from rest_framework import exceptions

logger = logging.getLogger(__name__)

SEED_DATA_FILE = None

def _get_users_csv_path():
    paths = [
        os.path.join(settings.BASE_DIR, "seed_data", "users.csv"),
        os.path.join(settings.BASE_DIR, "..", "seed_data", "users.csv"),
        "/openimis-be/seed_data/users.csv",
    ]
    for p in paths:
        if os.path.exists(p):
            return p
    return None


def load_users_from_csv():
    path = _get_users_csv_path()
    if not path:
        logger.warning("users.csv not found")
        return []
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def validate_user_against_csv(username, password):
    users = load_users_from_csv()
    for row in users:
        if row["username"] == username and row["password"] == password:
            return row
    return None


class CsvUserBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None):
        row = validate_user_against_csv(username, password)
        if row is None:
            return None
        user, created = User.objects.get_or_create(
            username=username,
            defaults={"is_staff": True},
        )
        if created:
            user.set_unusable_password()
            user.save()
        role = row.get("role", "staff")
        if role == "admin":
            user.is_superuser = True
            user.is_staff = True
            user.save()
        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


class CsvBasicAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        if not settings.DEMO_MODE:
            return None
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header.startswith("Basic "):
            if settings.DEMO_MODE:
                demo_user, _ = User.objects.get_or_create(
                    username="demo_admin",
                    defaults={"is_superuser": True, "is_staff": True},
                )
                return (demo_user, None)
            return None

        import base64
        try:
            credentials = base64.b64decode(auth_header[6:]).decode("utf-8")
            username, password = credentials.split(":", 1)
        except Exception:
            raise exceptions.AuthenticationFailed("Invalid Basic auth header")

        row = validate_user_against_csv(username, password)
        if row is None:
            raise exceptions.AuthenticationFailed("Invalid credentials")

        user, _ = User.objects.get_or_create(
            username=username,
            defaults={"is_staff": True},
        )
        role = row.get("role", "staff")
        if role == "admin":
            user.is_superuser = True
            user.is_staff = True
            user.save()
        return (user, None)
