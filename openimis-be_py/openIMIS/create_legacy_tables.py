import os
import sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'openIMIS.settings'
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import django
django.setup()
from django.db import connection
from django.apps import apps

cursor = connection.cursor()

# Get all models from all apps and create tables for unmanaged models
for app_config in apps.get_app_configs():
    for model in app_config.get_models():
        opts = model._meta
        if not opts.managed and opts.db_table:
            # Create the table with all fields
            cols = []
            for field in opts.fields:
                if field.is_relation and field.many_to_one:
                    continue 
                db_type = field.db_type(connection)
                if db_type:
                    null = "NULL" if field.null else "NOT NULL"
                    pk = "PRIMARY KEY" if field.primary_key else ""
                    default = ""
                    if field.has_default() and field.default is not None:
                        if isinstance(field.default, bool):
                            default = f"DEFAULT {'TRUE' if field.default else 'FALSE'}"
                        elif isinstance(field.default, (int, float)):
                            default = f"DEFAULT {field.default}"
                    col_def = f'"{field.db_column or field.column}" {db_type} {null} {pk} {default}'
                    cols.append(col_def.strip())
            
            sql = f'CREATE TABLE IF NOT EXISTS "{opts.db_table}" (\n    ' + ',\n    '.join(cols) + '\n)'
            try:
                cursor.execute(sql)
                print(f'Created table: {opts.db_table}')
            except Exception as e:
                print(f'Error creating {opts.db_table}: {e}')

print('Done creating legacy tables')
