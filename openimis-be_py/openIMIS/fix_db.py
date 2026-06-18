import os
import sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'openIMIS.settings'
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import django
django.setup()
from django.db import connection

cursor = connection.cursor()

# Create tblUsers table manually (needed for FK constraint from core_User)
cursor.execute("""
    CREATE TABLE IF NOT EXISTS "tblUsers" (
        "UserID" SERIAL PRIMARY KEY,
        "LegacyID" INTEGER,
        "LastName" VARCHAR(100),
        "OtherNames" VARCHAR(100),
        "Phone" VARCHAR(50),
        "LoginName" VARCHAR(50),
        "RoleID" INTEGER,
        "HFID" INTEGER,
        "ValidityFrom" TIMESTAMP,
        "ValidityTo" TIMESTAMP,
        "AuditUserID" INTEGER,
        "EmailId" VARCHAR(200),
        "LanguageID" INTEGER,
        "LastLogin" TIMESTAMP,
        "StoredPassword" VARCHAR(256),
        "PrivateKey" VARCHAR(256),
        "PasswordValidity" TIMESTAMP,
        "IsAssociated" BOOLEAN,
        "UUID" VARCHAR(36),
        "Json_ext" JSONB,
        "DateDeactivated" TIMESTAMP,
        "Active" BOOLEAN DEFAULT TRUE
    )
""")
print('Created tblUsers')

# Create other legacy tables that might be needed
cursor.execute("""
    CREATE TABLE IF NOT EXISTS "tblLanguages" (
        "LanguageCode" VARCHAR(2) PRIMARY KEY,
        "LanguageName" VARCHAR(50),
        "SortOrder" INTEGER
    )
""")
print('Created tblLanguages')

cursor.execute("""
    CREATE TABLE IF NOT EXISTS "tblRole" (
        "RoleID" SERIAL PRIMARY KEY,
        "RoleName" VARCHAR(50),
        "ValidityFrom" TIMESTAMP,
        "ValidityTo" TIMESTAMP,
        "AuditUserID" INTEGER
    )
""")
print('Created tblRole')

print('All legacy tables created successfully')
