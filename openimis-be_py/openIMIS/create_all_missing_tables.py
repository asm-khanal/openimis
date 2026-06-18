"""Create all tables that might be referenced by FK constraints.
This scans all managed models for FK references and creates any missing referenced tables."""
import os
import sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'openIMIS.settings'
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import django
django.setup()
from django.db import connection
from django.apps import apps

cursor = connection.cursor()

# Get all db_table names from models
all_tables = set()
fk_refs = set()
managed_tables = {}

for app_config in apps.get_app_configs():
    for model in app_config.get_models():
        opts = model._meta
        all_tables.add(opts.db_table)
        managed_tables[opts.db_table] = (model, opts.managed)
        
        # Collect FK references
        for field in opts.fields:
            if field.is_relation and field.related_model:
                related_table = field.related_model._meta.db_table
                if related_table and related_table != opts.db_table:
                    fk_refs.add(related_table)

# Find referenced tables that don't exist yet and might not be managed
missing = []
for tbl in fk_refs:
    existing = False
    try:
        cursor.execute(f'SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = %s)', [tbl.lower()])
        existing = cursor.fetchone()[0]
    except:
        pass
    if not existing and tbl in managed_tables:
        model, is_managed = managed_tables[tbl]
        if not is_managed:
            missing_tables.append(tbl)

print("Missing unmanaged referenced tables:")
for tbl in sorted(missing):
    print(f"  {tbl}")
