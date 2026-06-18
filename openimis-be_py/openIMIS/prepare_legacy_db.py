"""Parse all initial migration files and create all managed=False tables."""
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
    mig_dir = os.path.join(base_dir, 'core' if 'core_py' in base_dir else 
                           os.path.basename(base_dir).replace('openimis-be-', '').replace('_py', ''), 'migrations')
    if not os.path.exists(mig_dir):
        # Try alternative naming
        for root, dirs, files in os.walk(base_dir):
            for d in dirs:
                if d == 'migrations':
                    mig_dir = os.path.join(root, d)
                    break
    
    init_file = os.path.join(mig_dir, '0001_initial.py')
    if not os.path.exists(init_file):
        # Search deeper
        for root, dirs, files in os.walk(base_dir):
            if '0001_initial.py' in files:
                init_file = os.path.join(root, '0001_initial.py')
                break
    
    if not os.path.exists(init_file):
        continue
    
    content = open(init_file, 'r', encoding='utf-8').read()
    print(f"Processing: {init_file}")
    
    # Find CreateModel blocks with managed=False and extract db_table
    # Simple approach: find all db_table entries in CreateModel context
    blocks = content.split('migrations.CreateModel(')
    for block in blocks[1:]:
        # Check if managed=False is in this block
        if "'managed': False" in block or '"managed": False' in block:
            # Extract db_table
            m = re.search(r"['\"]db_table['\"]:\s*['\"]([^'\"]+)['\"]", block)
            if m:
                table_name = m.group(1)
                legacy_tables[table_name] = True
                print(f"  Found legacy table: {table_name}")

# Create all legacy tables (just with an id column)
for table_name in sorted(legacy_tables.keys()):
    try:
        cursor.execute(f'CREATE TABLE IF NOT EXISTS "{table_name}" ("id" SERIAL PRIMARY KEY)')
        print(f"Created: {table_name}")
    except Exception as e:
        print(f"Error creating {table_name}: {e}")

print(f"\nTotal legacy tables created: {len(legacy_tables)}")
