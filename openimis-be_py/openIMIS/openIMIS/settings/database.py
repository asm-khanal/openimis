import os

from .common import BASE_DIR

DATABASES = {}

if os.environ.get("NO_DATABASE", "False").lower() == "true":
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': str(BASE_DIR.parent / "script" / "sqlite-dev.db"),
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
else:
    PSQL_DATABASE_OPTIONS = {'options': '-c search_path=django,public'}
    DATABASES["default"] = {
        "ENGINE": os.environ.get("PSQL_DB_ENGINE", "django.db.backends.postgresql"),
        "NAME": os.environ.get("PSQL_DB_NAME", os.environ.get("DB_NAME", "imis")),
        "USER": os.environ.get("PSQL_DB_USER", os.environ.get("DB_USER", "IMISuser")),
        "PASSWORD": os.environ.get("PSQL_DB_PASSWORD", os.environ.get("DB_PASSWORD")),
        "HOST": os.environ.get("PSQL_DB_HOST", os.environ.get("DB_HOST", "db")),
        "PORT": os.environ.get("PSQL_DB_PORT", os.environ.get("DB_PORT", "5432")),
        "OPTIONS": PSQL_DATABASE_OPTIONS,
        'TEST': {
            'NAME': os.environ.get("DB_TEST_NAME", "test_" + os.environ.get("PSQL_DB_NAME", "imis")),
        }
    }

if "DASHBOARD_DB_ENGINE" in os.environ:
    DATABASES['dashboard_db'] = {
        "ENGINE": os.environ.get("DASHBOARD_DB_ENGINE", "django.db.backends.postgresql"),
        "NAME": os.environ.get("DASHBOARD_DB_NAME"),
        "USER": os.environ.get("DASHBOARD_DB_USER"),
        "PASSWORD": os.environ.get("DASHBOARD_DB_PASSWORD"),
        "HOST": os.environ.get("DASHBOARD_DB_HOST", os.environ.get("PSQL_DB_HOST", "db")),
        "PORT": os.environ.get("DASHBOARD_DB_PORT", os.environ.get("PSQL_DB_PORT", "5432"))
    }

MSSQL = False
DATABASE_ROUTERS = ["openIMIS.routers.DashboardDatabaseRouter"]

