import os
import sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'openIMIS.settings'
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import django
django.setup()
from django.db import connection
from django.apps import apps

cursor = connection.cursor()

# First gather all unmanaged model db_table names and their fields
# Also gather field info to create proper tables
all_unmanaged = {}
for app_config in apps.get_app_configs():
    for model in app_config.get_models():
        opts = model._meta
        if not opts.managed and opts.db_table:
            if opts.db_table not in all_unmanaged:
                fields_info = []
                for field in opts.fields:
                    if field.is_relation and (field.many_to_one or field.one_to_one):
                        continue  # Skip FK fields for table creation
                    db_type = field.db_type(connection)
                    if db_type:
                        fields_info.append({
                            'name': field.db_column or field.column,
                            'type': db_type,
                            'null': field.null,
                            'pk': field.primary_key,
                            'default': field.default if field.has_default() else None,
                        })
                all_unmanaged[opts.db_table] = fields_info

# Create each table
for table_name, fields in all_unmanaged.items():
    cols = []
    for f in fields:
        null_str = "NULL" if f['null'] else "NOT NULL"
        pk_str = "PRIMARY KEY" if f['pk'] else ""
        default_str = ""
        if f['default'] is not None and not f['pk']:
            if isinstance(f['default'], bool):
                default_str = f"DEFAULT {'TRUE' if f['default'] else 'FALSE'}"
            elif isinstance(f['default'], (int, float)):
                default_str = f"DEFAULT {f['default']}"
        col_def = f'    "{f["name"]}" {f["type"]} {null_str} {pk_str} {default_str}'.strip()
        cols.append(col_def)
    
    if cols:
        sql = f'CREATE TABLE IF NOT EXISTS "{table_name}" (\n' + ',\n'.join(cols) + '\n)'
        try:
            cursor.execute(sql)
            print(f'Created table: {table_name}')
        except Exception as e:
            print(f'Error creating {table_name}: {e}')

print(f'\nTotal unmanaged tables created: {len(all_unmanaged)}')
