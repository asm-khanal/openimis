# Clone Repos and Create Payment App Structure

## Task 1: Clone Required Repos into `d:\document\projects\openIMIS\`

Clone these repos at the root level (same level as `openimis-be_py`). The branches match what's declared in `openimis.json`.

**Core + Claims pipeline:**
| # | Repo | Branch | Why |
|---|------|--------|-----|
| 1 | `openimis/openimis-be-core_py` | `develop` | Base models (User, Officer, MutationLog), signals, JWT auth |
| 2 | `openimis/openimis-be-claim_py` | `develop` | Claim lifecycle — create, submit, validate, review, process |
| 3 | `openimis/openimis-be-claim_batch_py` | `chore/flake8-cleanup` | Batch processing of valued claims |

**Payment:**
| # | Repo | Branch | Why |
|---|------|--------|-----|
| 4 | `openimis/openimis-be-payment_py` | `develop` | Payment tracking models (PaymentType, Payment) |
| 5 | `openimis/openimis-be-payer_py` | `develop` | Payer entities (who funds) |

**Supporting (referenced by claims):**
| # | Repo | Branch | Why |
|---|------|--------|-----|
| 6 | `openimis/openimis-be-location_py` | `develop` | HealthFacility model |
| 7 | `openimis/openimis-be-medical_py` | `develop` | Diagnosis, Item, Service |
| 8 | `openimis/openimis-be-medical_pricelist_py` | `develop` | Price lists per location |
| 9 | `openimis/openimis-be-insuree_py` | `chore/flake8-cleanup` | Insured persons |
| 10 | `openimis/openimis-be-policy_py` | `develop` | Insurance policies (eligibility check) |
| 11 | `openimis/openimis-be-product_py` | `develop` | Benefit packages/coverage |

**Calculation rules (pricing engine):**
| # | Repo | Branch | Why |
|---|------|--------|-----|
| 12 | `openimis/openimis-be-calculation_py` | `develop` | Base calculation framework |
| 13 | `openimis/openimis-be-calcrule_third_party_payment_py` | `develop` | Fee-for-service calc |

Clone command pattern (PowerShell):
```
cd d:\document\projects\openIMIS
git clone -b <branch> https://github.com/openimis/<repo>.git
```

## Task 2: Install Cloned Modules as Editable Packages

After cloning, install each as editable so changes are picked up live:
```
cd d:\document\projects\openIMIS\<cloned-repo>
pip install -e .
```

## Task 3: Standalone Django App Structure (code later)

Create a new Django app inside `openimis-be_py/openIMIS/` called something like `hospital_payment` (or `direct_payment`). This app will:

```
openIMIS/
└── hospital_payment/
    ├── __init__.py
    ├── apps.py              # AppConfig, signal connections on ready()
    ├── models.py            # PaymentBatch, PaymentDetail, SOSYSSyncLog
    ├── services.py          # Core logic:
    │                        #   - fetch_approved_claims()
    │                        #   - validate_and_approve_claims()
    │                        #   - process_bulk_payment()
    │                        #   - sync_to_sosys()
    ├── sosys_client.py      # HTTP client to send payment details to SOSYS
    ├── admin.py             # Django admin for monitoring
    ├── management/
    │   └── commands/
    │       └── process_hospital_payments.py  # Management command to run bulk
    ├── signals.py           # Listen to claim signals (e.g., claim status → VALUATED)
    ├── tasks.py             # Celery tasks for async payment processing
    ├── urls.py              # REST endpoints for payment status/triggers
    ├── views.py             # API views (trigger payment, check status, SOSYS webhook)
    ├── serializers.py       # DRF serializers for payment data
    └── migrations/
        └── __init__.py
```

**Key responsibilities of this app:**
1. **Tap claims** — Listen to signals or query claims with `status = STATUS_VALUATED (16)` (approved and valued)
2. **Validate** — Re-validate or apply Nepal-specific business rules before payment
3. **Approve for payment** — Mark claims as selected for this payment cycle
4. **Bulk payment** — Group by health facility, calculate totals, create payment records
5. **Execute payment** — Call the actual payment mechanism (bank transfer, etc.)
6. **Sync to SOSYS** — After successful payment, POST payment details to SOSYS API
7. **Audit trail** — Log every step: which claims paid, amounts, SOSYS response

## Task 4: Register the New App

Add `hospital_payment` to `openimis.json` modules list and `INSTALLED_APPS` in `settings/base.py` so it's picked up by the modular system.
