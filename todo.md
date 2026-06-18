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

**File:** `openimis-be_py/requirements.txt`

Commented out (not needed for hackathon):
- `django-opensearch-dsl==0.5.1` — OpenSearch not used
- `django-csp` — CSP not needed for demo

Kept (required by code):
- `django-redis==5.4.0` — Required by `location/models.py` import (RedisCache class). LocMemCache is default, Redis not needed at runtime.

Already commented out (from earlier):
- `django-mssql-backend==2.8.1` / `mssql-django~=1.4` — PostgreSQL only
- `pyodbc` — PostgreSQL only

---

## REMAINING WORK

### Must Do Before Demo

- [ ] **Test Docker build:** Run `docker compose build` and `docker compose up` to verify the entire stack starts
- [ ] **Run seed data:** After containers start, exec into backend: `python manage.py seed_data`
- [ ] **Verify migrations:** Ensure `python manage.py migrate` runs without errors for all 13 modules
- [ ] **Test payment flow:** Submit a claim → valuate it → create payment batch → approve → verify API call to ngrok URL

### Known Potential Issues

1. **`sentry-requirements.txt`** — Still installed in Dockerfile (`RUN pip install -r sentry-requirements.txt`). Contains only `sentry_sdk` and `urllib3` — safe.

2. **`opensearch.py` settings file** — Still included in settings `__init__.py`. It just sets dict values (doesn't import anything), so it won't break, but the OPENSEARCH_DSL config points to a non-existent host. Harmless.

3. **`seed_data` command** — The `SEED_DIR` path detection may need adjustment depending on where the command runs (local vs Docker). In Docker, it looks for `/openimis-be/seed_data/`.

### Fixed Issues (no longer pending)

- ~~`channels-redis` / `channels-rabbitmq`~~ — Commented out (not needed, no Redis)
- ~~`report` module from GitHub~~ — Cloned locally, now uses `-e ../openimis-be-report_py`
- ~~`openimis.json` had 4 duplicate JSON blocks~~ — Fixed to single valid JSON
- ~~Sibling modules not bind-mounted in Docker~~ — All 13 modules now mounted in both backend and worker
- ~~`policy` missing `calculation`/`contribution_plan`~~ — Both modules cloned and added back
- ~~`git+` apscheduler dependency~~ — Replaced with PyPI `django-apscheduler==0.6.2`
- ~~All `git+` URLs removed~~ — `requirements.txt` and `openimis.json` are 100% local/offline

### Nice to Have (Post-Hackathon)

- [ ] Frontend reduction (mentioned in reduction.md but not started)
- [ ] Reconciliation system (sending paid claims to SOSYS afterward)
- [ ] More CSV data (user asked for "lakhs" — current is ~50 families, can scale with `--families` flag)
- [ ] Proper authentication instead of demo bypass
- [ ] Production Dockerfile stage (pre-install modules during build)

---

## How to Run

### Local Development
```bash
cd d:\document\projects\openIMIS\openimis-be_py
# Install modules locally
cd script
python modules-requirements.py ../openimis.json > modules-requirements.txt
pip install -r modules-requirements.txt
# Run migrations
cd ../openIMIS
python manage.py migrate
# Load seed data
python manage.py seed_data --families 50
# Start server
python manage.py runserver
```

### Docker
```bash
cd d:\document\projects\openIMIS\openimis-be_py
docker compose up --build
# In another terminal, load seed data:
docker exec -it dev-backend python manage.py seed_data
```

### API Endpoints (Hospital Payment)

| Method | URL | Purpose |
|--------|-----|---------|
| GET | `/api/hospital_payment/` | List payment batches |
| POST | `/api/hospital_payment/` | Create payment batch from valuated claims |
| GET | `/api/hospital_payment/<id>/` | Get batch detail with claims |
| POST | `/api/hospital_payment/approve/` | Approve batch (triggers Celery payment task) |
| POST | `/api/hospital_payment/webhook/` | Payment API webhook (no auth) |
| GET | `/api/hospital_payment/records/` | List payment records |

GraphQL endpoint: `/api/graphql/` (queries: `hospitalPaymentBatches`, `hospitalPaymentBatch`, `hospitalPaymentRecords`)

---

## Key File Locations

```
d:\document\projects\openIMIS\
├── openimis-be_py/                    # Main backend project
│   ├── openimis.json                  # 13 modules (reduced from 44)
│   ├── .env                           # Docker config + DEMO_NO_AUTH=True
│   ├── .env.example                   # Template with Docker notes
│   ├── .dockerignore                  # Excludes unnecessary files
│   ├── docker-compose.yml             # 4 services: db, rabbitmq, backend, worker
│   ├── Dockerfile                     # MSSQL commented out
│   ├── requirements.txt               # OpenSearch/Redis/CSP commented out
│   ├── seed_data/                     # CSV files for seeding
│   │   ├── locations.csv
│   │   ├── reference_data.csv
│   │   ├── diagnoses.csv
│   │   ├── items.csv
│   │   ├── services.csv
│   │   ├── products.csv
│   │   └── health_facilities.csv
│   └── openIMIS/
│       └── openIMIS/
│           └── settings/
│               ├── base.py            # DemoAuth middleware added, OpenSearch/CSP removed
│               ├── __init__.py        # Includes opensearch.py (harmless)
│               └── security.py        # ROW_SECURITY setting
│
├── openimis-be-hospital_payment_py/   # Custom payment module
│   ├── setup.py                       # Deps: core, claim, location
│   └── hospital_payment/
│       ├── apps.py                    # Payment API URL: ngrok URL
│       ├── models.py                  # 4 models
│       ├── services.py                # Batch creation, API call, webhook
│       ├── views.py                   # 5 REST endpoints
│       ├── urls.py                    # Routes
│       ├── serializers.py             # DRF serializers
│       ├── schema.py                  # GraphQL queries/mutations
│       ├── tasks.py                   # Celery async payment
│       ├── signals.py                 # Signal binding stub
│       ├── admin.py                   # Admin registration
│       ├── middleware.py              # DemoAuthenticationMiddleware
│       ├── migrations/
│       │   └── 0001_initial.py        # All 4 models
│       └── management/
│           └── commands/
│               └── seed_data.py       # CSV loader + data generator
│
├── openimis-be-core_py/               # Core module (cloned)
├── openimis-be-location_py/           # Location module (cloned)
├── openimis-be-insuree_py/            # Insuree module (cloned)
├── openimis-be-medical_py/            # Medical module (cloned)
├── openimis-be-medical_pricelist_py/  # Medical pricelist (cloned)
├── openimis-be-product_py/            # Product module (cloned)
├── openimis-be-claim_py/              # Claim module (cloned)
├── openimis-be-claim_batch_py/        # Claim batch (cloned)
├── openimis-be-policy_py/             # Policy module (cloned)
├── openimis-be-payment_py/            # Payment module (cloned, NOT in openimis.json)
├── reduction.md                       # Original requirements doc
└── plan_for_sending_claims.md         # Original implementation plan
```

---

## Payment Flow (End to End)

```
1. Hospital submits claim (via GraphQL mutation or REST)
   → Claim enters STATUS_ENTERED (2)

2. Claim validation runs (claim/validations.py — 2032 lines)
   → 9-step pipeline: date → insuree/policy → pricelist → category limits → items → services → product → status → dedrem
   → If valid: STATUS_VALUATED (16)

3. Admin opens hospital_payment API → sees valuated claims grouped by hospital
   → POST /api/hospital_payment/ creates HospitalPaymentBatch + HospitalPaymentBatchClaim records

4. Admin approves batch
   → POST /api/hospital_payment/approve/ sets STATUS_APPROVED
   → Celery task `process_payment_batch_task` fires

5. Celery worker calls payment API
   → POST to https://convolutional-intertwistingly-madge.ngrok-free.dev
   → Payload: batch_reference, hospital info, claims list, amounts
   → No auth header (api_key is empty)

6. Payment API responds
   → process_payment_response() updates batch + claim statuses
   → Creates HospitalPaymentRecord with raw response

7. External payment API sends webhook
   → POST /api/hospital_payment/webhook/ (no auth)
   → process_webhook_payment_confirmation() updates final payment status
```

---

## Task Tracker

| ID | Task | Status |
|----|------|--------|
| r1 | Analyze module dependencies | ✅ Complete |
| r2 | Reduce openimis.json + fix setup.py | ✅ Complete (13 modules, all local paths) |
| r3 | Create CSV seed data files | ✅ Complete (7 CSV files) |
| r4 | Create management command | ✅ Complete (seed_data.py) |
| r5 | Remove/simplify authentication | ✅ Complete (demo middleware) |
| r6 | Update requirements.txt | ✅ Complete (no git+ URLs, no OpenSearch/Redis/CSP) |
| r7 | Update reduction.md | ✅ Complete |
| r8 | Fix openimis.json (4 duplicate JSON blocks) | ✅ Complete |
| r9 | Bind-mount all modules in docker-compose.yml | ✅ Complete |
| r10 | Clone report module locally | ✅ Complete |
| r11 | Add calculation + contribution_plan back | ✅ Complete (policy FK dependency) |
| r12 | Replace git+ apscheduler with PyPI version | ✅ Complete |
| dc1-dc7 | Docker fixes | ✅ Complete |
| 1-18 | Hospital payment module | ✅ Complete |
| d1 | Docker build + up | ⬜ Pending (requires Docker Desktop running) |
| d2 | Verify migrations inside container | ⬜ Pending |
| d3 | Run seed_data inside container | ⬜ Pending |
| d4 | Test full payment flow | ⬜ Pending |
