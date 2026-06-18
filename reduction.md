### **Current**
- This is the total openimis backend
- Here, we have all the services that the openimis uses
- We are trying to do the tapping system where we tap the claims of the hospitals ask for the payment after the person do the treamtment under health insurance
- In the previous or the openimis implementation in nepal, the openimis had to send the data of the bundle of the claim of money to the SOSYS
- Now we are have tried to implement the system, where we are trying to send reuquest of payement directly from the openimis to the payement gateway by simulating the payement gateway
- The whole backend is too large and trying to clone from the repo from github 
- rather than runnning all the system
- we need to keep what is needed
    - **What actually is needed?**
        - We need the hospitals sending the claims on money to openimis, in the current system there is the database entity and atrrubutes and we will not change that.
        - We also need the backend of validating that claim are valid based on what we have
        - But keepign all the apis endpoint we need to enter the users, then enter hospitals and we donot need to do that all to show for hackathon 
        - We can seed those data in csvs and manage the code to do so
        - Keeping the hospitals claming the money, then validating, then bundling and then asking the payement gateway to pay that with the adminstator clicking to pay(check is implemented), and then after payment the payment system api sending back the payed amount, the openIMIS upadting what is paid
        - We can seed the hospitals entered, the disease which are paid for by healht insurance and the registered families etc in csv as per the db design currently implemented
        - then we will reduce the current frontend to the part we need
        - Also no need to keep the current hosptial authenitcation(login part)
        - Change the all the current implementation of the graph ql to psotegres only and then add the serailziers or validators, update views,schemmas and the urls required right now


### **What will we do in the next time or future?**
- Then do the work on reconcillation by first sending the payed claimed from the openIMIS to the SOSYS.
- we will then to reconcillation, make system to handle.

### **What to do?*
- Delete the file unrequrieed
- Clone to required repo to local
- Striclty update the current docker to what we need
- As per the current db design seed the csv file with lakhs of data and then update the sysytem to use csv 

This is done to make the system and docker lightweight and timely and enoguh for hackathon 

---

## Completed Work Summary

### 1. Module Reduction (44 → 13 modules)
- Reduced `openimis.json` from 44 modules to 13 essential modules
- **Kept:** core, location, insuree, medical, medical_pricelist, product, claim_batch, claim, calculation, contribution_plan, policy, report, hospital_payment
- All modules now use local `-e ../openimis-be-*` paths (no git+ URLs — works offline)
- **Report module** cloned locally from GitHub to `openimis-be-report_py/`
- **Calculation + contribution_plan** added back (policy has FK to ContributionPlan)

### 2. Hospital Payment Module (custom, 14+ files)
- Location: `openimis-be-hospital_payment_py/hospital_payment/`
- **Models (4):** HospitalPaymentBatch, HospitalPaymentBatchClaim, HospitalPaymentRecord, HospitalPaymentMutation
- **REST API (5 endpoints):** list/create batches, batch detail, approve, webhook (no auth), payment records
- **Services:** batch creation from valuated claims, approval flow, external payment API call, webhook processing
- **Celery task:** async payment processing after admin approval
- **GraphQL:** queries + mutations in schema.py
- **Demo auth middleware:** auto-login as admin superuser when `DEMO_NO_AUTH=True`
- **Seed data command:** `python manage.py seed_data` loads 7 CSVs + generates families/insurees/policies

### 3. Docker Configuration
- **docker-compose.yml:** 4 services (db, rabbitmq, backend, worker)
- **All 11 modules bind-mounted** in both backend and worker services
- MSSQL and OpenSearch commented out
- PostgreSQL-only deployment
- Celery worker for async payment processing
- **docker-compose.yml validated** — no errors

### 4. Seed Data (7 CSV files)
- Location: `openimis-be_py/seed_data/`
- locations.csv (13 rows — Nepal regions/districts/municipalities)
- reference_data.csv (genders, family types, legal forms, sub levels, relations)
- diagnoses.csv (56 ICD-10 codes), items.csv (15), services.csv (15)
- products.csv (3 insurance products), health_facilities.csv (10 Nepal hospitals)

### 5. Bugs Fixed
- **CRITICAL:** `openimis.json` had 4 duplicate JSON blocks — fixed to single valid JSON with 13 modules
- **channels-redis / channels-rabbitmq** commented out — not needed, no Redis running
- **report module** switched from `git+` URL to local path — avoids GitHub dependency in Docker
- **calculation + contribution_plan** added back — `policy` has FK dependency that cannot be lazy-loaded
- **git+ apscheduler** replaced with PyPI `django-apscheduler==0.6.2` — SQL Server fork not needed for PostgreSQL
- **All 13 modules bind-mounted** in docker-compose for both backend and worker services

### 6. Configuration
- `.env`: `DEMO_NO_AUTH=True`, `ROW_SECURITY=False`, `PSQL_DB_HOST=db`, PostgreSQL only
- `requirements.txt`: OpenSearch, Redis, CSP, channels-redis, channels-rabbitmq commented out; git+ apscheduler replaced with PyPI
- `base.py`: DemoAuth middleware added, OpenSearch/CSP removed
- All 13 modules use local paths — Docker build works fully offline (zero git+ URLs)

### To Run
```bash
# Start Docker Desktop first, then:
cd openimis-be_py
docker compose up --build
# In another terminal:
docker exec -it dev-backend python manage.py seed_data
```
