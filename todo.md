# TODO — openIMIS Hospital Payment Module (Hackathon)

## Project Overview

Building a **direct hospital payment flow** for Nepal's openIMIS implementation. Instead of sending claims to external SOSYS for payment, this system:
1. Collects approved (VALUATED) claims per hospital in bulk
2. Admin approves payment batches
3. Payment API is called (simulated at `https://convolutional-intertwistingly-madge.ngrok-free.dev`)
4. Payment API sends back confirmation → openIMIS updates payment records
5. No human intervention needed after admin approval

The backend has been **reduced from 44 modules to 13** for a lightweight hackathon deployment.

---

## COMPLETED WORK

### 1. Hospital Payment Module (14 files + 4 new files = 18 total)

**Location:** `d:\document\projects\openIMIS\openimis-be-hospital_payment_py\hospital_payment\`

| File | Status | Purpose |
|------|--------|---------|
| `__init__.py` | ✅ Done | App config pointer |
| `apps.py` | ✅ Done | HospitalPaymentConfig, permissions, payment API URL |
| `models.py` | ✅ Done | 4 models: HospitalPaymentBatch, HospitalPaymentBatchClaim, HospitalPaymentRecord, HospitalPaymentMutation |
| `serializers.py` | ✅ Done | DRF serializers for REST API |
| `services.py` | ✅ Done | Batch creation, approval, payment API call, webhook processing |
| `views.py` | ✅ Done | 5 REST endpoints: list/create, detail, approve, webhook (no auth), records |
| `urls.py` | ✅ Done | 5 routes |
| `tasks.py` | ✅ Done | Celery task for async payment processing |
| `signals.py` | ✅ Done | Stub for signal binding |
| `admin.py` | ✅ Done | Django admin registration |
| `schema.py` | ✅ Done | GraphQL queries + mutations |
| `migrations/0001_initial.py` | ✅ Done | Initial migration with all 4 models |
| `setup.py` | ✅ Done | Package setup (deps: core, claim, location — payment removed) |
| `middleware.py` | ✅ Done | DemoAuthenticationMiddleware — auto-login for hackathon |
| `management/commands/seed_data.py` | ✅ Done | Loads CSVs + generates families/insurees/policies |

**Key config in `apps.py`:**
- `payment_api_url` = `https://convolutional-intertwistingly-madge.ngrok-free.dev`
- `payment_api_key` = `""` (no key needed for simulated API)
- Permission codes: 131801-131806

### 2. Module Reduction (44 → 13 modules)

**File:** `openimis-be_py/openimis.json`

**Kept modules (13):** core, location, insuree, medical, medical_pricelist, product, claim_batch, claim, calculation, contribution_plan, policy, report, hospital_payment

**Note:** `calculation` and `contribution_plan` were added back because `policy` has a ForeignKey to `ContributionPlan` and uses `calculation.services.run_calculation_rules`.

**Removed modules (31):** individual, workflow, tasks_management, contribution, payer, payment, tools, api_fhir_r4, policyholder, contract, invoice, all calcrule_*, im_export, dhis2_etl, social_protection, opensearch_reports, payment_cycle, payroll, controls, grievance_social_protection, claim_sampling, deduplication, api_etl

**Dependency chain verified:**
- `claim` imports from `claim_batch` (models.py) and `report` (views.py) — both kept
- `hospital_payment` setup.py deps: django, djangorestframework, openimis-be-core, openimis-be-claim, openimis-be-location (payment removed)

### 3. Docker Configuration

**Files modified:**
- `docker-compose.yml` — 4 services: `db` (PostgreSQL), `rabbitmq`, `backend`, `worker`. MSSQL and OpenSearch commented out.
- `Dockerfile` — MSSQL client installation commented out (lines 18-21)
- `.env` — Created with Docker-appropriate values (`PSQL_DB_HOST=db`, `CELERY_BROKER_URL=amqp://rabbitmq:5672`, `DEMO_NO_AUTH=True`, `ROW_SECURITY=False`)
- `.env.example` — Updated with note about `PSQL_DB_HOST=db` for Docker
- `.dockerignore` — Created to exclude unnecessary files
- `package.json` / `package-lock.json` — Deleted (accidental, unrelated to Python backend)

**Docker compose services:**
- `db`: PostgreSQL on port 5432
- `rabbitmq`: RabbitMQ on ports 5672 (AMQP) + 15672 (management UI)
- `backend`: Django server on port 8000 (installs modules at runtime, runs migrations, starts server)
- `worker`: Celery worker for async payment processing

**hospital_payment module in Docker:**
- Bind-mounted: `../openimis-be-hospital_payment_py:/openimis-be/openimis-be-hospital_payment_py`
- The `-e ../openimis-be-hospital_payment_py` in openimis.json resolves correctly inside container

### 4. CSV Seed Data Files

**Location:** `openimis-be_py/seed_data/`

| CSV File | Rows | Content |
|----------|------|---------|
| `locations.csv` | 13 | 3 Regions, 5 Districts, 5 Municipalities (Nepal) |
| `reference_data.csv` | 24 | Genders (3), FamilyTypes (2), LegalForms (3), SubLevels (3), Relations (6) |
| `diagnoses.csv` | 56 | ICD-10 diagnosis codes (A00 through T14) |
| `items.csv` | 15 | Medical items (Paracetamol, Amoxicillin, IV fluids, etc.) |
| `services.csv` | 15 | Medical services (consultations, X-ray, surgery, etc.) |
| `products.csv` | 3 | Insurance products (Basic, Premium, Family Floater) |
| `health_facilities.csv` | 10 | Nepal hospitals (TUTH, Bir Hospital, Patan, etc.) |

**Families/Insurees/Policies:** Generated programmatically by `seed_data` management command (50 families default, ~3-5 members each, active policies for all).

### 5. Seed Data Management Command

**File:** `hospital_payment/management/commands/seed_data.py`

**Usage:**
```bash
python manage.py seed_data                    # Load all seed data (50 families)
python manage.py seed_data --families 100     # Generate 100 families
python manage.py seed_data --clean            # Delete existing data first
```

**What it does:**
1. Loads locations from CSV
2. Creates reference data (genders, family types, legal forms, sub levels, relations)
3. Loads diagnoses, items, services from CSV
4. Loads products and health facilities from CSV
5. Generates N families with head + spouse + 1-3 children (Nepali names)
6. Creates active policies for all families with InsureePolicy links

### 6. Authentication Simplification (Hackathon Demo)

**File:** `hospital_payment/middleware.py` — `DemoAuthenticationMiddleware`

**How it works:**
- When `DEMO_NO_AUTH=True` in `.env`, all requests auto-authenticate as an admin superuser
- No login/JWT token needed for any API endpoint
- Creates a demo admin user (username="admin") if one doesn't exist
- The payment webhook endpoint (`/api/hospital_payment/webhook/`) already has no auth (permission_classes=[])

**Settings changes in `base.py`:**
- Added `"hospital_payment.middleware.DemoAuthenticationMiddleware"` to MIDDLEWARE
- Added `DEMO_NO_AUTH = os.environ.get("DEMO_NO_AUTH", "false").lower() == "true"`
- Removed `"django_opensearch_dsl"` from INSTALLED_APPS
- Removed `"csp.middleware.CSPMiddleware"` from MIDDLEWARE

**`.env` additions:**
- `DEMO_NO_AUTH=True`
- `ROW_SECURITY=False`

### 7. Requirements Cleanup
## TODO — Agent action plan (clear, actionable steps)

Purpose: a compact checklist an automated agent can follow to prepare a hackathon-ready deployment (backend + minified frontend + seeded demo data).

Status legend: [ ] not-started  [~] in-progress  [x] done

Priority tasks
- [~] 1) Validate backend repo and migrations
   - Run inside `openimis-be_py`: `python manage.py migrate --check` and fix any migration errors.
   - Acceptance: `manage.py migrate` completes without errors.

- [ ] 2) Run seed data and verify seeded entities
   - Command: `python manage.py seed_data --families 50` (or `docker exec -it dev-backend python manage.py seed_data` when using Docker).
   - Acceptance: `tblFamily`, `tblInsuree`, `tblPolicy`, and `tblHealthFacility` have expected rows.

- [ ] 3) Test hospital payment flow end-to-end (manual or automated test)
   - Steps:
      - Create/submit/process a claim to reach `STATUS_VALUATED` (16).
      - POST to `/api/hospital_payment/` to build a batch.
      - POST to `/api/hospital_payment/approve/` and verify Celery task enqueues and executes.
      - Confirm the external POST was made (logs) and `HospitalPaymentRecord` created.
   - Acceptance: claims updated to paid/remunerated and records created.

- [ ] 4) Build reduced frontend (minified)
   - Edit `frontend/openimis-dev.json` or `frontend/openimis.json` to include only required FE modules (home, claim, payment, core, product, policy as needed).
   - Commands:
      - `cd frontend`
      - `yarn install`
      - `yarn build`
   - Acceptance: `dist/` (or build output) contains minified assets and homepage + payment UI work against backend.

- [ ] 5) Docker validation (compose)
   - Commands (from `openimis-be_py`):
      - `docker compose up --build -d`
      - `docker compose logs -f backend` (watch for migrations/seeding messages)
   - Acceptance: containers `db`, `rabbitmq`, `backend`, `worker` are running, backend responds on port 8000.

Optional/cleanup tasks
- [ ] A) Remove unused frontend modules and files from the assembly repo (if size is an issue).
- [ ] B) Increase seed size: run `python manage.py seed_data --families 5000` for load testing.
- [ ] C) Replace `DEMO_NO_AUTH` with proper auth for production (post-hackathon).

Agent notes / commands to run
- To run backend checks locally (venv):
   ```powershell
   cd d:\document\projects\openIMIS\openimis-be_py\openIMIS
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   pip install -r ../requirements.txt
   python manage.py migrate
   python manage.py seed_data --families 50
   ```
- To run quickly with Docker (recommended for demo):
   ```powershell
   cd d:\document\projects\openIMIS\openimis-be_py
   docker compose up --build -d
   docker exec -it dev-backend python manage.py seed_data --families 50
   ```

Keep this file updated: when the agent completes a step, mark the checkbox and add a one-line log with date and brief outcome.

----

Modified: concise actionable plan for your agent to execute the hackathon tasks.
python manage.py migrate
