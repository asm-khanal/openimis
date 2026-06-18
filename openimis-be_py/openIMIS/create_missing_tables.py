import os
import sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'openIMIS.settings'
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import django
django.setup()
from django.db import connection
import re

cursor = connection.cursor()

# Collect all managed models that have FK to unmanaged models
# and create the referenced unmanaged tables
# From the migration files and model inspection

LEGACY_TABLES = {
    "tblLocations": """
        CREATE TABLE IF NOT EXISTS "tblLocations" (
            "LocationId" SERIAL PRIMARY KEY,
            "LocationCode" VARCHAR(10),
            "LocationName" VARCHAR(50),
            "LocationType" VARCHAR(1),
            "ParentLocationId" INTEGER,
            "LegacyID" INTEGER,
            "ValidityFrom" TIMESTAMP,
            "ValidityTo" TIMESTAMP,
            "AuditUserID" INTEGER,
            "OffLine" BOOLEAN DEFAULT FALSE,
            "RowID" BYTEA
        )
    """,
    "tblHF": """
        CREATE TABLE IF NOT EXISTS "tblHF" (
            "HfID" SERIAL PRIMARY KEY,
            "LegacyID" INTEGER,
            "HFCode" VARCHAR(10),
            "HFName" VARCHAR(100),
            "HFNameExt" VARCHAR(100),
            "HFLevel" VARCHAR(1),
            "LegalForm" VARCHAR(1),
            "HFCareType" VARCHAR(1),
            "HFSublevel" INTEGER,
            "LocationId" INTEGER,
            "ValidityFrom" TIMESTAMP,
            "ValidityTo" TIMESTAMP,
            "AuditUserID" INTEGER,
            "OffLine" BOOLEAN DEFAULT FALSE,
            "RowID" BYTEA
        )
    """,
    "tblLegalForms": """
        CREATE TABLE IF NOT EXISTS "tblLegalForms" (
            "LegalFormCode" VARCHAR(1) PRIMARY KEY,
            "LegalFormName" VARCHAR(50),
            "SortOrder" INTEGER,
            "AltLanguage" VARCHAR(50)
        )
    """,
    "tblHFSublevel": """
        CREATE TABLE IF NOT EXISTS "tblHFSublevel" (
            "HFSublevelID" SERIAL PRIMARY KEY,
            "HFLevel" VARCHAR(1),
            "HFSublevelName" VARCHAR(50),
            "SortOrder" INTEGER,
            "AltLanguage" VARCHAR(50)
        )
    """,
    "tblHFCatchment": """
        CREATE TABLE IF NOT EXISTS "tblHFCatchment" (
            "HFCatchmentId" SERIAL PRIMARY KEY,
            "HFID" INTEGER,
            "LocationId" INTEGER,
            "ValidityFrom" TIMESTAMP,
            "ValidityTo" TIMESTAMP,
            "AuditUserID" INTEGER
        )
    """,
    "tblUsersDistricts": """
        CREATE TABLE IF NOT EXISTS "tblUsersDistricts" (
            "UserDistrictID" SERIAL PRIMARY KEY,
            "UserID" INTEGER,
            "DistrictId" INTEGER,
            "ValidityFrom" TIMESTAMP,
            "ValidityTo" TIMESTAMP,
            "AuditUserID" INTEGER
        )
    """,
    "tblOfficerVillages": """
        CREATE TABLE IF NOT EXISTS "tblOfficerVillages" (
            "OfficerVillageID" SERIAL PRIMARY KEY,
            "OfficerID" INTEGER,
            "LocationId" INTEGER,
            "ValidityFrom" TIMESTAMP,
            "ValidityTo" TIMESTAMP,
            "AuditUserID" INTEGER
        )
    """,
    "tblClaimAdmin": """
        CREATE TABLE IF NOT EXISTS "tblClaimAdmin" (
            "ClaimAdminId" SERIAL PRIMARY KEY,
            "LegacyID" INTEGER,
            "ClaimAdminCode" VARCHAR(50),
            "LastName" VARCHAR(100),
            "OtherNames" VARCHAR(100),
            "DOB" DATE,
            "EmailId" VARCHAR(200),
            "Phone" VARCHAR(50),
            "HFId" INTEGER,
            "ValidityFrom" TIMESTAMP,
            "ValidityTo" TIMESTAMP,
            "AuditUserId" INTEGER,
            "HasLogin" BOOLEAN DEFAULT FALSE,
            "ClaimAdminUUID" VARCHAR(36)
        )
    """,
    "tblOfficer": """
        CREATE TABLE IF NOT EXISTS "tblOfficer" (
            "OfficerID" SERIAL PRIMARY KEY,
            "OfficerCode" VARCHAR(50),
            "LastName" VARCHAR(100),
            "OtherNames" VARCHAR(100),
            "DOB" DATE,
            "EmailId" VARCHAR(200),
            "Phone" VARCHAR(50),
            "HFId" INTEGER,
            "ValidityFrom" TIMESTAMP,
            "ValidityTo" TIMESTAMP,
            "AuditUserID" INTEGER,
            "HasLogin" BOOLEAN DEFAULT FALSE,
            "OfficerUUID" VARCHAR(36)
        )
    """,
    "tblInsuree": """
        CREATE TABLE IF NOT EXISTS "tblInsuree" (
            "InsureeID" SERIAL PRIMARY KEY,
            "LegacyID" INTEGER,
            "InsureeUUID" VARCHAR(36),
            "CHFID" VARCHAR(20),
            "LastName" VARCHAR(100),
            "OtherNames" VARCHAR(100),
            "DOB" DATE,
            "Gender" VARCHAR(1),
            "Marital" VARCHAR(1),
            "Phone" VARCHAR(50),
            "Email" VARCHAR(200),
            "Passport" VARCHAR(20),
            "CurrentVillage" INTEGER,
            "CardIssued" BOOLEAN DEFAULT FALSE,
            "Relationship" INTEGER,
            "ValidityFrom" TIMESTAMP,
            "ValidityTo" TIMESTAMP,
            "AuditUserID" INTEGER,
            "Json_ext" JSONB
        )
    """,
    "tblClaim": """
        CREATE TABLE IF NOT EXISTS "tblClaim" (
            "ClaimID" SERIAL PRIMARY KEY,
            "LegacyID" INTEGER,
            "ClaimUUID" VARCHAR(36),
            "CHFID" VARCHAR(20),
            "ClaimDate" DATE,
            "DateClaimed" DATE,
            "DateReceived" DATE,
            "DateProcessed" DATE,
            "HFID" INTEGER,
            "ICDCode" VARCHAR(20),
            "ClaimAdmin" INTEGER,
            "HealthFacility" INTEGER,
            "ValidityFrom" TIMESTAMP,
            "ValidityTo" TIMESTAMP,
            "AuditUserID" INTEGER,
            "Json_ext" JSONB
        )
    """,
}

for name, sql in LEGACY_TABLES.items():
    try:
        cursor.execute(sql)
        print(f'Created table: {name}')
    except Exception as e:
        print(f'Error creating {name}: {e}')

print('Done')
