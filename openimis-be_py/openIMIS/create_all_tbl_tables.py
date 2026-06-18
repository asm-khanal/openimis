"""Create all legacy tbl* tables to support FK constraints during migrations."""
import os
import sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'openIMIS.settings'
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import django
django.setup()
from django.db import connection
from django.apps import apps

cursor = connection.cursor()

# Collect all models with db_table starting with 'tbl'
legacy_tables = {}
for app_config in apps.get_app_configs():
    for model in app_config.get_models():
        opts = model._meta
        if opts.db_table and (opts.db_table.startswith('tbl') or opts.db_table.startswith('core_') or opts.db_table.startswith('location_') or opts.db_table.startswith('product_') or opts.db_table.startswith('insuree_') or opts.db_table.startswith('medical_') or opts.db_table.startswith('contribution_') or opts.db_table.startswith('claim_') or opts.db_table.startswith('policy_') or opts.db_table.startswith('invoice_') or opts.db_table.startswith('report_')):
            if opts.db_table not in legacy_tables:
                fields_info = []
                for field in opts.local_fields:
                    if field.is_relation and (field.many_to_one or field.one_to_one):
                        # Add just an integer column for FK
                        fk_name = field.db_column or (field.name + '_id')
                        fields_info.append({
                            'name': fk_name,
                            'type': 'INTEGER',
                            'null': True,
                            'pk': False,
                        })
                    else:
                        db_type = field.db_type(connection)
                        if db_type:
                            fields_info.append({
                                'name': field.db_column or field.column,
                                'type': db_type,
                                'null': field.null,
                                'pk': field.primary_key,
                            })
                legacy_tables[opts.db_table] = fields_info

# Create tables
count = 0
for table_name, fields in legacy_tables.items():
    cols = []
    pk_found = False
    for f in fields:
        null_str = "NULL" if f['null'] else "NOT NULL"
        pk_str = "PRIMARY KEY" if f['pk'] else ""
        if f['pk']:
            pk_found = True
        col_def = f'"{f["name"]}" {f["type"]} {null_str} {pk_str}'.strip()
        cols.append(col_def)
    
    if not pk_found:
        cols.insert(0, '"id" SERIAL PRIMARY KEY')
    
    sql = 'CREATE TABLE IF NOT EXISTS "{}" (\n  {}\n)'.format(table_name, ',\n  '.join(cols))
    try:
        cursor.execute(sql)
        print(f'OK: {table_name}')
        count += 1
    except Exception as e:
        print(f'ERR: {table_name}: {e}')

print(f'\nCreated {count} tables')
