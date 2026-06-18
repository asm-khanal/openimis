# openIMIS Claims → Direct Payment → SOSYS Sync: Complete Flow

## Table of Contents
- [Phase 0: Django Boot Sequence](#phase-0-django-boot-sequence)
- [Phase 1: Request Arrives — Middleware Chain](#phase-1-request-arrives--middleware-chain)
- [Phase 2: Hospital Creates a Claim](#phase-2-hospital-creates-a-claim)
- [Phase 3: Hospital Submits the Claim](#phase-3-hospital-submits-the-claim)
- [Phase 4: Review (Feedback & Review Cycle)](#phase-4-review-feedback--review-cycle)
- [Phase 5: Process Claims (Valuation)](#phase-5-process-claims-valuation)
- [Phase 6: Batch Run (For PROCESSED Claims)](#phase-6-batch-run-for-processed-claims)
- [Phase 7: Direct Hospital Payment + SOSYS Sync](#phase-7-direct-hospital-payment--sosys-sync)
- [Complete File Map](#complete-file-map-all-files-involved)
- [Claim Status State Machine](#claim-status-state-machine)

---

## Phase 0: Django Boot Sequence

Every file listed here is touched **once** when the server starts, before any request is handled.

```
manage.py runserver  (or server.py via Waitress)
    │
    ├── os.environ['DJANGO_SETTINGS_MODULE'] = 'openIMIS.settings'
    │
    ├── openIMIS/settings/__init__.py
    │       Loads .env file, then calls split_settings in this order:
    │       ├── settings/common.py          → BASE_DIR, MODE, DEBUG
    │       ├── settings/security.py        → AUTH model (core.User), JWT, Axes, rate limits, CSP
    │       ├── settings/base.py            → INSTALLED_APPS (dynamic via openimisapps.py),
    │       │                                  MIDDLEWARE, REST_FRAMEWORK, GRAPHENE config
    │       ├── settings/database.py        → PostgreSQL/MSSQL connection
    │       ├── settings/logging.py         → Log handlers
    │       ├── settings/sentry.py          → Error tracking
    │       ├── settings/scheduler.py       → APScheduler
    │       ├── settings/queue_cache.py     → Redis/Celery queue
    │       ├── settings/opensearch.py      → Search engine
    │       ├── settings/trad.py            → Translation (i18n)
    │       └── settings/{dev|prod}.py      → Environment-specific overrides
    │
    ├── openIMIS/__init__.py
    │       Imports celery app → celery.py
    │       Celery autodiscovers tasks from all INSTALLED_APPS
    │
    ├── openIMIS/openIMIS/openimisapps.py
    │       Reads openimis.json → extracts module list
    │       Topologically sorts modules by dependency (from each module's setup.py)
    │       Returns ordered list: [core, location, medical, insuree, policy, product, claim, ...]
    │       All modules added to INSTALLED_APPS
    │
    ├── Each module's apps.py → AppConfig.ready()
    │       ├── core/apps.py           → Loads core module config from DB
    │       ├── claim/apps.py          → Loads claim config (permissions, validation flags)
    │       ├── payment/apps.py        → Loads payment config
    │       └── ...
    │
    ├── openIMIS/signal_binding/apps.py → ready()
    │       For each module: imports {module}.signals → calls bind_service_signals()
    │       This wires up inter-module service signals (e.g., claim ↔ payment)
    │
    ├── openIMIS/receiver_binding/apps.py → ready()
    │       For each module: imports {module}.receivers
    │       This wires up Django signal receivers
    │
    ├── openIMIS/openIMIS/schema.py → Module level
    │       For each module: imports {module}.schema
    │       Collects all Query and Mutation classes
    │       Calls bind_signals() on each module's schema.py
    │       Merges into unified GraphQL schema:
    │         class Query(*all_module_queries, ObjectType)
    │         class Mutation(*all_module_mutations, ObjectType)
    │         schema = graphene.Schema(query=Query, mutation=Mutation)
    │
    └── openIMIS/openIMIS/urls.py
            URL patterns mounted:
            ├── /admin/           → Django admin
            ├── /graphql          → OpenIMISGraphQLView (with jwt_cookie)
            ├── /health/          → Health check
            └── openimisurls.py   → Dynamic: /claim/, /payment/, /core/, etc.
```

---

## Phase 1: Request Arrives — Middleware Chain

When a hospital user sends a GraphQL request (e.g., `POST /graphql` with a `createClaim` mutation):

```
HTTP Request → WSGI (wsgi.py / server.py)
    │
    ├── Django Middleware Stack (order matters):
    │   ├── SecurityMiddleware           → HTTPS redirect, CSP headers, HSTS
    │   ├── WhiteNoiseMiddleware         → Static files
    │   ├── RateLimitMiddleware          → 150 req/min per user
    │   ├── AxesMiddleware               → Brute-force protection (5 fails → 5 min lockout)
    │   ├── SessionMiddleware            → Session cookies
    │   ├── CsrfViewMiddleware           → CSRF token validation
    │   ├── AuthenticationMiddleware     → Attaches user to request
    │   ├── CSPMiddleware                → Content Security Policy headers
    │   └── (Custom exception handler)   → ExceptionHandlerDispatcher.py
    │         Extracts module name from URL path
    │         Routes exceptions to module-specific handlers
    │
    └── openIMIS/openIMIS/views.py → OpenIMISGraphQLView.dispatch()
            ├── Reads JWT from cookie or Authorization header
            ├── Validates JWT (RS256 or HS256) → authenticates user
            ├── Parses GraphQL query
            ├── For mutations: wraps in transaction.atomic()
            ├── Executes against unified schema
            └── Returns JSON response
```

---

## Phase 2: Hospital Creates a Claim

**GraphQL mutation**: `createClaim(input: {...})`

```
GraphQL Schema (unified)
    │
    ├── claim/schema.py → Mutation.create_claim → CreateClaimMutation.Field()
    │
    ├── core/schema.py → OpenIMISMutation.mutate_and_get_payload()
    │   │
    │   ├── 1. Creates MutationLog record (audit trail)
    │   │
    │   ├── 2. Sends signal_mutation signal (global)
    │   │
    │   ├── 3. Sends signal_mutation_module_validate["claim"]
    │   │       └── claim/schema.py → on_claim_mutation()
    │   │           Creates ClaimMutation linking claim ↔ mutation_log
    │   │
    │   ├── 4. Sends signal_mutation_module_before_mutating["claim"]
    │   │
    │   ├── 5. Calls CreateClaimMutation.async_mutate(user, **data)
    │   │       └── claim/gql_mutations.py → CreateClaimMutation.async_mutate()
    │   │           ├── Checks permissions (111002)
    │   │           ├── Sets status = STATUS_ENTERED (2)
    │   │           ├── Calls update_or_create_claim(data, user)
    │   │           │   └── claim/services.py → validate_claim_data()
    │   │           │       ├── Checks claim code uniqueness
    │   │           │       ├── Validates diagnosis count
    │   │           │       ├── Validates code length
    │   │           │       └── Validates restore logic (if applicable)
    │   │           │   └── claim/services.py → claim_create()
    │   │           │       ├── Claim.objects.create(**data)  → DB insert
    │   │           │       └── claim_create_items_and_services()
    │   │           │           ├── process_items_relations() → ClaimItem rows
    │   │           │           └── process_services_relations() → ClaimService rows
    │   │           └── Creates attachments (if any)
    │   │
    │   ├── 6. On success: mutation_log.mark_as_successful()
    │   │   On failure: mutation_log.mark_as_failed(errors_json)
    │   │
    │   └── 7. Sends signal_mutation_module_after_mutating["claim"]
    │           └── claim/schema.py → on_claim_after_mutation()
    │               Handles autogenerate code logging
    │
    └── Response: { createClaim { clientMutationId } }
```

**Claim status**: `STATUS_ENTERED (2)` — saved in `tblClaim`

---

## Phase 3: Hospital Submits the Claim

**GraphQL mutation**: `submitClaims(uuids: ["..."])`

```
claim/schema.py → Mutation.submit_claims → SubmitClaimsMutation
    │
    ├── core/schema.py → OpenIMISMutation.mutate_and_get_payload()
    │   (same signal flow as Phase 2)
    │
    └── claim/gql_mutations.py → SubmitClaimsMutation.async_mutate()
        │
        ├── Checks permissions (111007)
        │
        ├── For each claim UUID:
        │   └── claim/services.py → ClaimSubmitService.submit_claim()
        │       │
        │       ├── _validate_submit_permissions()
        │       ├── _validate_user_hf() → Row-level security check
        │       ├── claim.save_history() → VersionedModel audit copy
        │       │
        │       ├── processing_claim(claim, user, is_process=False)
        │       │   ├── get_claim_target_date(claim)
        │       │   ├── get_valid_policies_qs(insuree, date) → Active insurance policies
        │       │   │
        │       │   └── claim/validations.py → validate_claim()
        │       │       ├── fetch_policies() → No policy = REJECTED
        │       │       ├── fetch_items_and_services()
        │       │       ├── For each item/service:
        │       │       │   ├── Check item/service exists
        │       │       │   ├── Check in price list (medical_pricelist)
        │       │       │   ├── Check product coverage (product module)
        │       │       │   ├── Check category limitations (OP/IP)
        │       │       │   ├── Check frequency limits
        │       │       │   ├── Check waiting periods
        │       │       │   ├── Check max visits/consultations/surgeries
        │       │       │   ├── Check quantity limits
        │       │       │   └── Check care type (O=Outpatient, I=Inpatient)
        │       │       │
        │       │       └── Returns errors[] (empty = valid)
        │       │
        │       ├── If errors:
        │       │   └── __submit_to_rejected() → status = STATUS_REJECTED (1)
        │       │
        │       └── If valid:
        │           └── __submit_to_checked()
        │               ├── approved = approved_amount(claim)
        │               ├── status = STATUS_CHECKED (4)
        │               ├── category = get_claim_category()
        │               └── claim.save()
        │
        └── add_submission_stats_to_mutation_log()
```

**Claim status**: `STATUS_CHECKED (4)` or `STATUS_REJECTED (1)`

---

## Phase 4: Review (Feedback & Review Cycle)

```
selectClaimsForFeedback → feedback_status = FEEDBACK_SELECTED (4)
deliverClaimFeedback    → feedback_status = FEEDBACK_DELIVERED (8)
selectClaimsForReview   → review_status = REVIEW_SELECTED (4)
saveClaimReview         → Adjust items/services prices, update status
deliverClaimsReview     → review_status = REVIEW_DELIVERED (8)
                          + update_claims_dedrems() → Recalculate deductions
bypassClaimsReview      → review_status = REVIEW_BYPASSED (16)
skipClaimsReview        → review_status = REVIEW_NOT_SELECTED (2)
```

---

## Phase 5: Process Claims (Valuation)

**GraphQL mutation**: `processClaims(uuids: ["..."])`

```
claim/schema.py → Mutation.process_claims → ProcessClaimsMutation
    │
    └── claim/gql_mutations.py → ProcessClaimsMutation.async_mutate()
        │
        ├── Checks permissions (111011)
        │
        └── For each claim:
            ├── claim.save_history()
            ├── claim/gql_mutations.py → processing_claim(claim, user, is_process=True)
            │   └── claim/services.py → processing_claim()
            │       ├── Validate claim again (full validation)
            │       ├── Assign products to items/services
            │       ├── Process dedrem (deductibles & remuneration)
            │       │   └── Creates ClaimDedRem records
            │       │
            │       └── set_claim_processed_or_valuated()
            │           ├── If relative prices exist:
            │           │   └── status = STATUS_PROCESSED (8)
            │           │       (needs batch run to finalize)
            │           │
            │           └── If no relative prices:
            │               └── status = STATUS_VALUATED (16)
            │                   valuated = approved amount
            │                   (ready for payment immediately)
            │
            └── claim.save()
```

**Claim status**: `STATUS_PROCESSED (8)` or `STATUS_VALUATED (16)`

---

## Phase 6: Batch Run (For PROCESSED Claims)

```
claim_batch/schema.py → Mutation.process_batch → ProcessBatchMutation
    │
    └── claim_batch/services.py → process_batch()
        │
        ├── Creates BatchRun record (location, year, month)
        │
        ├── Queries all STATUS_PROCESSED claims for this location/month
        │
        ├── For each claim:
        │   ├── Apply relative pricing (capitation/fee-for-service)
        │   ├── Calculate final valuated amounts
        │   └── Update claim: status = STATUS_VALUATED (16)
        │
        └── Links claims to batch_run
```

---

## Phase 7: Direct Hospital Payment + SOSYS Sync

This is the new standalone app that replaces the old "send to SOSYS" flow.

```
┌─────────────────────────────────────────────────────────────────────┐
│  hospital_payment/ (new Django app inside openimis-be_py/openIMIS/) │
└─────────────────────────────────────────────────────────────────────┘

Trigger Options (how claims enter this app):
    A) Celery Beat task (scheduled, e.g., daily/weekly)
    B) Management command (manual: python manage.py process_hospital_payments)
    C) Signal listener (on claim status → VALUATED)
    D) REST API endpoint (manual trigger)

FLOW:
─────

Step 1: FETCH VALUATED CLAIMS
    services.py → fetch_approved_claims()
    ├── Query: Claim.objects.filter(status=16, batch_run__isnull=False)
    ├── Group by health_facility
    └── Calculate per-HF totals

Step 2: VALIDATE FOR PAYMENT (Nepal-specific rules)
    services.py → validate_claims_for_payment(claims)
    ├── Check claim is VALUATED and not already paid
    ├── Check HF bank details exist
    ├── Check no duplicate payment
    └── Apply any Nepal-specific business rules

Step 3: APPROVE FOR PAYMENT
    services.py → approve_claims_for_payment(claims)
    ├── Mark claims as "selected for payment cycle"
    ├── Create PaymentBatch record
    └── Create PaymentDetail per claim

Step 4: EXECUTE BULK PAYMENT
    services.py → process_bulk_payment(batch)
    ├── Group PaymentDetails by health_facility
    ├── For each HF:
    │   ├── Calculate total amount
    │   ├── Call payment gateway / bank API
    │   └── Record transaction reference
    └── Update PaymentBatch status

Step 5: SYNC TO SOSYS
    sosys_client.py → sync_to_sosys(batch)
    ├── Build payload: {
    │     hospital_code, hospital_name,
    │     total_amount, payment_date,
    │     transaction_ref,
    │     claims: [{claim_code, insuree_chfid, amount, ...}]
    │   }
    ├── POST to SOSYS API endpoint
    ├── Log response in SOSYSSyncLog
    └── Retry on failure (Celery retry)

Step 6: UPDATE CLAIM STATUS
    services.py → mark_claims_paid(claims)
    ├── Update claim status to REMUNERATED
    ├── Record payment date
    └── Create audit trail entries
```

---

## Complete File Map (All Files Involved)

### Boot & Configuration

| File | Role |
|------|------|
| `openimis-be_py/openIMIS/manage.py` | Entry point, sets DJANGO_SETTINGS_MODULE |
| `openimis-be_py/openIMIS/server.py` | Waitress WSGI server |
| `openimis-be_py/openIMIS/openIMIS/wsgi.py` | WSGI application |
| `openimis-be_py/openIMIS/openIMIS/__init__.py` | Imports Celery app |
| `openimis-be_py/openIMIS/openIMIS/celery.py` | Celery config, autodiscover tasks |
| `openimis-be_py/openIMIS/openIMIS/settings/__init__.py` | Split settings loader |
| `openimis-be_py/openIMIS/openIMIS/settings/common.py` | BASE_DIR, MODE, DEBUG |
| `openimis-be_py/openIMIS/openIMIS/settings/security.py` | Auth, JWT, rate limits |
| `openimis-be_py/openIMIS/openIMIS/settings/base.py` | INSTALLED_APPS, middleware, REST/GraphQL config |
| `openimis-be_py/openIMIS/openIMIS/settings/database.py` | DB connection |
| `openimis-be_py/openimis.json` | Module declarations |

### Module Discovery & Wiring

| File | Role |
|------|------|
| `openimis-be_py/openIMIS/openIMIS/openimisapps.py` | Reads openimis.json, topological sort |
| `openimis-be_py/openIMIS/openIMIS/schema.py` | Merges all module schemas into unified GraphQL |
| `openimis-be_py/openIMIS/openIMIS/openimisurls.py` | Dynamic URL routing per module |
| `openimis-be_py/openIMIS/openIMIS/urls.py` | Main URL config (admin, graphql, health) |
| `openimis-be_py/openIMIS/signal_binding/apps.py` | Binds service signals at startup |
| `openimis-be_py/openIMIS/receiver_binding/apps.py` | Binds receivers at startup |

### Request Handling

| File | Role |
|------|------|
| `openimis-be_py/openIMIS/openIMIS/views.py` | GraphQL view — JWT auth, mutation execution, atomic transactions |
| `openimis-be_py/openIMIS/openIMIS/ExceptionHandlerDispatcher.py` | Routes exceptions to module handlers |
| `openimis-be_py/openIMIS/openIMIS/ExceptionHandlerRegistry.py` | Exception handler registry |

### Core Module (openimis-be-core_py)

| File | Role |
|------|------|
| `core/signals.py` | Signal system: `register_service_signal`, `bind_service_signal`, priority-based Signal |
| `core/schema.py` | `OpenIMISMutation` base class, mutation signals, MutationLog |
| `core/models.py` | User, Officer, MutationLog, VersionedModel, ExtendableModel |

### Claim Module (openimis-be-claim_py)

| File | Role |
|------|------|
| `claim/apps.py` | ClaimConfig — permissions, validation settings |
| `claim/schema.py` | GraphQL Query + Mutation, `bind_signals()`, `on_claim_mutation()` |
| `claim/gql_mutations.py` | All mutation classes: Create, Update, Submit, Process, Review, etc. |
| `claim/gql_queries.py` | GraphQL query resolvers |
| `claim/services.py` | Business logic: `ClaimSubmitService`, `ClaimCreateService`, `processing_claim()` |
| `claim/validations.py` | 2000+ lines of claim validation (eligibility, pricing, limits) |
| `claim/models.py` | Claim, ClaimItem, ClaimService, ClaimDedRem, Feedback, ClaimAttachment |
| `claim/urls.py` | REST endpoints (print, attach) |
| `claim/views.py` | REST views for printing/attachments |

### Batch Module (openimis-be-claim_batch_py)

| File | Role |
|------|------|
| `claim_batch/models.py` | BatchRun, RelativeIndex, CapitationPayment |
| `claim_batch/services.py` | `process_batch()` — batch valuation of claims |
| `claim_batch/schema.py` | GraphQL mutations for batch processing |

### Payment Module (openimis-be-payment_py)

| File | Role |
|------|------|
| `payment/models.py` | Payment, PaymentDetail, PaymentMutation |
| `payment/signals.py` | `signal_before_payment_query` |
| `payment/services.py` | Payment processing services |
| `payment/schema.py` | GraphQL schema |

### New App: hospital_payment (to be created)

| File | Role |
|------|------|
| `hospital_payment/__init__.py` | Package init |
| `hospital_payment/apps.py` | AppConfig, signal connections |
| `hospital_payment/models.py` | PaymentBatch, PaymentDetail, SOSYSSyncLog |
| `hospital_payment/services.py` | fetch, validate, approve, pay, mark_paid |
| `hospital_payment/sosys_client.py` | HTTP client for SOSYS API |
| `hospital_payment/signals.py` | Listen to claim VALUATED signal |
| `hospital_payment/tasks.py` | Celery async tasks |
| `hospital_payment/views.py` | REST API (trigger, status, webhook) |
| `hospital_payment/serializers.py` | DRF serializers |
| `hospital_payment/urls.py` | URL routes |
| `hospital_payment/admin.py` | Django admin |
| `hospital_payment/management/commands/process_hospital_payments.py` | CLI command |
| `hospital_payment/migrations/__init__.py` | Migrations package |

---

## Claim Status State Machine

```
STATUS_ENTERED (2)
    │
    ├── Submit → STATUS_CHECKED (4)     [valid]
    │            STATUS_REJECTED (1)    [invalid]
    │
    ├── Review → STATUS_PROCESSED (8)   [relative prices]
    │            STATUS_VALUATED (16)   [absolute prices]
    │
    ├── Batch  → STATUS_VALUATED (16)   [after batch run]
    │
    ├── NEW: Payment → REMUNERATED      [after direct payment]
    │
    └── NEW: SOSYS Sync → SYNCED        [after SOSYS confirmation]
```

---

## Key Signal Flow (How Modules Communicate)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SIGNAL ARCHITECTURE                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1. signal_mutation (global)                                        │
│     └── Fired on EVERY mutation                                     │
│                                                                      │
│  2. signal_mutation_module_validate["claim"]                        │
│     └── Fired BEFORE mutation executes                              │
│     └── claim/schema.py → on_claim_mutation()                       │
│                                                                      │
│  3. signal_mutation_module_before_mutating["claim"]                 │
│     └── Fired just before async_mutate()                            │
│                                                                      │
│  4. signal_mutation_module_after_mutating["claim"]                  │
│     └── Fired after async_mutate() completes                        │
│     └── claim/schema.py → on_claim_after_mutation()                 │
│                                                                      │
│  5. register_service_signal("claim.submit_claim")                   │
│     └── Fires before/after service method execution                 │
│     └── Other modules can hook into claim submission                │
│                                                                      │
│  6. signal_claim_rejection (Django dispatch.Signal)                 │
│     └── Fired when claim items/services are rejected                │
│                                                                      │
│  7. signal_before_payment_query                                     │
│     └── Fired before payment queries                                │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Authentication & Authorization Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│  1. Hospital user sends POST /graphql with JWT in header/cookie     │
│                                                                      │
│  2. OpenIMISGraphQLView.dispatch()                                  │
│     ├── Extract JWT from Authorization header or cookie             │
│     ├── Validate JWT signature (RS256 or HS256)                     │
│     ├── Decode payload → user_id, exp, iat                          │
│     ├── Load user from DB: core.User.objects.get(id=user_id)        │
│     └── Attach user to request.context                              │
│                                                                      │
│  3. Permission checks at each mutation:                             │
│     ├── CreateClaim: 111002                                         │
│     ├── UpdateClaim: 111010                                         │
│     ├── SubmitClaim: 111007                                         │
│     ├── ProcessClaim: 111011                                        │
│     ├── DeliverReview: 111008                                       │
│     └── DeliverFeedback: 111009                                     │
│                                                                      │
│  4. Row-level security (if ROW_SECURITY=True):                      │
│     └── Filter claims by user's health_facility                     │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Database Tables Involved

| Table | Module | Purpose |
|-------|--------|---------|
| `tblClaim` | claim | Main claims table |
| `tblClaimItems` | claim | Claim line items (medicines, supplies) |
| `tblClaimServices` | claim | Claim line services (procedures, consultations) |
| `tblClaimDedRem` | claim | Deductibles & remuneration per claim |
| `tblFeedback` | claim | Patient feedback on claim |
| `tblFeedbackPrompt` | claim | Feedback prompt sent to officer |
| `tblClaimAttachments` | claim | Documents attached to claim |
| `tblBatchRun` | claim_batch | Batch processing records |
| `tblRelIndex` | claim_batch | Relative pricing indices |
| `tblPayment` | payment | Payment records |
| `tblPaymentDetails` | payment | Payment line items |
| `tblClaimMutation` | claim | Links claims to mutation logs |
| `tblMutationLog` | core | Audit trail for all mutations |

---

## Summary: End-to-End Data Flow

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│ Hospital │────▶│ openIMIS │────▶│  Batch   │────▶│ Payment  │
│  (HF)    │     │  Claim   │     │  Run     │     │  Module  │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
     │                │                │                │
     │  1. Create     │  3. Submit     │  5. Process    │
     │  claim         │  claim         │  claims        │
     │                │                │                │
     │  STATUS=2      │  STATUS=4      │  STATUS=8/16   │
     │  (ENTERED)     │  (CHECKED)     │  (PROCESSED/   │
     │                │                │   VALUATED)    │
     │                │                │                │
     │                │                │         ┌──────┴──────┐
     │                │                │         │             │
     │                │                │         ▼             ▼
     │                │                │  ┌──────────┐  ┌──────────┐
     │                │                │  │  NEW:    │  │  SOSYS   │
     │                │                │  │ hospital │  │  Sync    │
     │                │                │  │ _payment │  │  (POST)  │
     │                │                │  └──────────┘  └──────────┘
     │                │                │       │             │
     │                │                │       ▼             ▼
     │                │                │  STATUS=PAID   STATUS=SYNCED
```
