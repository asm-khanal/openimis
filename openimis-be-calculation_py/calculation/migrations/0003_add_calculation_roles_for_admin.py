import logging

from django.db import migrations

from core.utils import insert_role_right_for_system

logger = logging.getLogger(__name__)


def add_rights(apps, schema_editor):
    insert_role_right_for_system(64, 153001, apps)  # calculation
    insert_role_right_for_system(64, 153003, apps)  # calculation update


class Migration(migrations.Migration):
    dependencies = [
        ('calculation', '0002_auto_20210118_1426')
    ]

    operations = [
        migrations.RunPython(add_rights),
    ]
