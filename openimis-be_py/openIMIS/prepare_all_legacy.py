"""Parse ALL migration files and create all managed=False tables."""
import os
import re
import sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'openIMIS.settings'

import django
django.setup()
from django.db import connection

cursor = connection.cursor()

# Directories to search for migration files
search_dirs = [
    os.path.join(os.path.dirname(__file__), '..', '..', 'openimis-be-core_py'),
    os.path.join(os.path.dirname(__file__), '..', '..', 'openimis-be-location_py'),
    os.path.join(os.path.dirname(__file__), '..', '..', 'openimis-be-insuree_py'),
    os.path.join(os.path.dirname(__file__), '..', '..', 'openimis-be-medical_py'),
    os.path.join(os.path.dirname(__file__), '..', '..', 'openimis-be-medical_pricelist_py'),
    os.path.join(os.path.dirname(__file__), '..', '..', 'openimis-be-product_py'),
    os.path.join(os.path.dirname(__file__), '..', '..', 'openimis-be-payer_py'),
    os.path.join(os.path.dirname(__file__), '..', '..', 'openimis-be-calculation_py'),
    os.path.join(os.path.dirname(__file__), '..', '..', 'openimis-be-contribution_plan_py'),
    os.path.join(os.path.dirname(__file__), '..', '..', 'openimis-be-contribution_py'),
    os.path.join(os.path.dirname(__file__), '..', '..', 'openimis-be-invoice_py'),
    os.path.join(os.path.dirname(__file__), '..', '..', 'openimis-be-claim_batch_py'),
    os.path.join(os.path.dirname(__file__), '..', '..', 'openimis-be-claim_py'),
    os.path.join(os.path.dirname(__file__), '..', '..', 'openimis-be-policy_py'),
    os.path.join(os.path.dirname(__file__), '..', '..', 'openimis-be-report_py'),
    os.path.join(os.path.dirname(__file__), '..', '..', 'openimis-be-hospital_payment_py'),
]

legacy_tables = {}

for base_dir in search_dirs:
    # Walk all migration files
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith('.py') and file != '__init__.py':
                filepath = os.path.join(root, file)
                content = open(filepath, 'r', encoding='utf-8').read()
                
                # Find CreateModel blocks with managed=False
                markers = ['migrations.CreateModel(', 'CreateModel(']
                for marker in markers:
                    blocks = content.split(marker)
                    for block in blocks[1:]:
                        if "'managed': False" in block or '"managed": False' in block:
                            m = re.search(r"['\"]db_table['\"]:\s*['\"]([^'\"]+)['\"]", block)
                            if m:
                                table_name = m.group(1)
                                legacy_tables[table_name] = True

print(f"Found {len(legacy_tables)} legacy tables to create:")
for t in sorted(legacy_tables.keys()):
    print(f"  {t}")

# Create all legacy tables (just with an id column)
for table_name in sorted(legacy_tables.keys()):
    try:
        cursor.execute(f'CREATE TABLE IF NOT EXISTS "{table_name}" ("id" SERIAL PRIMARY KEY)')
        print(f"Created: {table_name}")
    except Exception as e:
        print(f"Error creating {table_name}: {e}")

print(f"\nDone! Created {len(legacy_tables)} tables")
