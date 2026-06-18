import os
import sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'openIMIS.settings'
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import django
django.setup()
from django.db import connection

cursor = connection.cursor()

cursor.execute('ALTER TABLE "tblOfficer" ADD COLUMN IF NOT EXISTS "Code" VARCHAR(50)')
print('Added Code column to tblOfficer')

cursor.execute('ALTER TABLE "tblOfficer" ADD COLUMN IF NOT EXISTS "Json_ext" JSONB')
print('Added Json_ext column to tblOfficer')

cursor.execute('ALTER TABLE "tblInsuree" ADD COLUMN IF NOT EXISTS "Code" VARCHAR(50)')
print('Added Code column to tblInsuree')

cursor.execute('ALTER TABLE "tblClaimAdmin" ADD COLUMN IF NOT EXISTS "Code" VARCHAR(50)')
print('Added Code column to tblClaimAdmin')

print('Done fixing columns')
