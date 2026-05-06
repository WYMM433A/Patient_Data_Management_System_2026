# PDMS — Project Status Report
**Patient Data Management System | University IT Project**
**Date: April 2026 | Stack: Python FastAPI + SQL Server + HTML/CSS/TypeScript**

---

## What This System Is

An outpatient clinic management system for small-to-medium GP clinics. Manages the full patient journey from registration → appointment → clinical encounter → diagnosis → prescriptions → lab → discharge.

**NOT** a hospital system — no inpatient wards, no billing, no pharmacy inventory, no HL7/FHIR.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.13, FastAPI, SQLAlchemy 2.0, pyodbc |
| Database | Microsoft SQL Server (local Windows Auth) |
| Auth | JWT access + refresh tokens, bcrypt (direct, no passlib) |
| Frontend | HTML / CSS / TypeScript (in progress by partner) |
| AI (planned) | OpenAI GPT-4o-mini |
| Server | uvicorn, port 8000 |
| Swagger UI | http://localhost:8000/docs |

---

## System Roles (6)

| Role | Key Access |
|---|---|
| system_admin | User management, audit logs |
| doctor | Encounters, SOAP, diagnoses, prescriptions, lab orders, referrals, care plans |
| nurse | Vitals, vaccinations, patient view |
| receptionist | Patient registration, appointments |
| lab_technician | View orders, upload results |
| patient | Portal — own records only (not yet built) |

---

## Database — 22 Tables

### Group 1: RBAC
- **roles** — role_id PK, role_name (unique), description
- **permissions** — permission_id PK, permission_name (unique), module, action
- **role_permissions** — junction: role_id + permission_id (composite PK)
- **users** — user_id PK, username, password_hash, email, role_id FK→roles, first_name, last_name, is_active

### Group 2: Patients
- **patients** — patient_id PK, mrn (PDMS-YYYY-NNNNN, unique), first_name, last_name, dob, gender, blood_type, phone, email, address, emergency contact
- **medical_history** — history_id PK, patient_id FK, condition_name, icd_code, onset_date, is_chronic, is_removed (soft delete), recorded_by FK→users
- **allergies** — allergy_id PK, patient_id FK, allergen, reaction_type, severity (mild/moderate/severe), is_removed (soft delete), recorded_by FK→users
- **vaccinations** — vaccination_id PK, patient_id FK, vaccine_name, dose_number, administered_by FK→users, administered_at, next_due_date

### Group 3: Scheduling
- **appointments** — appointment_id PK, patient_id FK, doctor_id FK→users, scheduled_at, reason, status (scheduled/confirmed/checked_in/completed/cancelled), checked_at, created_by FK→users

### Group 4: Clinical Encounters
- **encounters** — encounter_id PK, patient_id FK, doctor_id FK, appointment_id FK (nullable = walk-in), encounter_type (outpatient/follow-up/emergency), chief_complaint, status (open/closed), visit_number, closed_at
- **clinical_notes** — note_id PK, encounter_id FK (1-to-1), doctor_id FK, subjective, objective, assessment, plan (SOAP format), recorded_at, updated_at
- **vitals** — vital_id PK, encounter_id FK (1-to-many), patient_id FK, recorded_by FK, BP sys/dia, heart_rate, temperature, weight_kg, height_cm, O2 sat, respiratory_rate, bmi (AUTO by trigger), is_abnormal (AUTO by trigger)
- **diagnoses** — diagnosis_id PK, encounter_id FK (1-to-many), patient_id FK, icd_code, description, diagnosis_type (primary/secondary), condition (suspected/confirmed/excluded/recurrent), timing (acute/chronic/complication/recurrence), is_chronic, diagnosed_by FK

### Group 5: Medications
- **prescriptions** — prescription_id PK, encounter_id FK (1-to-many), patient_id FK, doctor_id FK, drug_name, dosage, frequency, duration, route (oral/IV/topical/inhaled/subcutaneous), is_active, is_removed (soft delete)

### Group 6: Diagnostics
- **lab_test_templates** — template_id PK, test_name, test_code (unique e.g. "CBC"), test_category, is_active
- **lab_test_parameters** — parameter_id PK, template_id FK (1-to-many), parameter_name, unit, normal_range_min/max, value_type (numeric/text/positive_negative), display_order
- **lab_orders** — order_id PK, encounter_id FK, patient_id FK, ordered_by FK, template_id FK (optional), test_name/code/category (denormalized), priority (routine/urgent/stat), status (ordered/in-progress/completed)
- **lab_results** — result_id PK, order_id FK (1-to-many — one per parameter), patient_id FK, parameter_id FK (optional), uploaded_by FK, parameter_name, result_value, unit, normal_range (denormalized), is_abnormal, abnormal_level (low/borderline/high/critical), validated_by FK
- **imaging_records** — imaging_id PK, encounter_id FK, patient_id FK, ordered_by FK, imaging_type (X-ray/Ultrasound/MRI/CT/ECG), body_part, findings, image_url, radiologist_notes

### Group 7: Care Coordination
- **referrals** — referral_id PK, encounter_id FK, patient_id FK, referred_by FK, specialty, reason, urgency (routine/urgent), status (pending/accepted/completed)
- **care_plans** — plan_id PK, patient_id FK, doctor_id FK, condition, goals, interventions, start_date, review_date, status (active/completed/cancelled)

### Group 8: Audit
- **audit_logs** — log_id PK, user_id FK (nullable), action (CREATE/UPDATE/DELETE/VIEW), module, table_affected, record_id, old_value (JSON), new_value (JSON), ip_address, timestamp. INSERT-ONLY — populated by DB triggers.

---

## Advanced DB Concepts Implemented

| Concept | Implementation |
|---|---|
| Normalization | All 22 entities in 3NF/BCNF |
| Stored Procedures | `usp_create_encounter` (ACID — creates encounter + empty SOAP note atomically + auto visit number), `usp_record_prescription` (allergy safety check — returns error if drug conflicts with patient allergy) |
| Triggers | `trg_calculate_bmi` on vitals INSERT, `trg_flag_abnormal_vitals` on vitals INSERT, `trg_audit_*` on all clinical tables (INSERT/UPDATE/DELETE → writes to audit_logs) |
| ACID Transactions | All stored procs use BEGIN TRY/CATCH + COMMIT/ROLLBACK |
| Indexing | On patient_id, encounter_date, doctor_id, is_abnormal, ordered_at, icd_code |
| Full-Text Search | FTS index on clinical_notes and diagnoses — CONTAINS() queries |
| JSON Storage | audit_logs.old_value + new_value stored via FOR JSON PATH |
| Soft Delete | is_removed BIT on allergies, medical_history, prescriptions |
| Audit Trail | Every INSERT/UPDATE/DELETE on clinical tables auto-logged by triggers |

---

## Backend Architecture

```
HTTP Request
  → routers/      (endpoint + permission guard: require_permission("permission_name"))
  → services/     (business logic + DB queries)
  → models/       (SQLAlchemy ORM ↔ SQL Server)
  ↑
  schemas/        (Pydantic — validate input / shape output)
  ↑
  core/security.py (JWT decoded → current_user injected into protected routes)
```

**Key quirks:**
- All PKs are UNIQUEIDENTIFIER — SQLAlchemy uses str(uuid) when querying
- Tables with audit triggers MUST have `__table_args__ = {"implicit_returning": False}` on the SQLAlchemy model — otherwise SQL Server's OUTPUT clause conflicts with the trigger
- bcrypt used directly (not passlib — passlib incompatible with bcrypt >= 4.0)
- Login uses `OAuth2PasswordRequestForm` (form-encoded, not JSON) for Swagger Authorize button compatibility
- EmailStr replaced with plain str (email-validator rejects .local domains)
- MSSQL requires ORDER BY whenever OFFSET/LIMIT is used

---

## Completed Modules (17/19)

| # | Module | Key Endpoints |
|---|---|---|
| 1 | Project scaffold | GET /health |
| 2 | Database schema | 13 SQL files in /database/ |
| 3 | Auth | POST /auth/login, POST /auth/refresh |
| 4 | RBAC + Users | GET/POST/PATCH/DELETE /users, GET /users/roles |
| 5 | Patients | CRUD /patients + medical-history, allergies, vaccinations sub-resources |
| 6 | Appointments | book/reschedule/cancel/list + POST /appointments/{id}/check-in |
| 7 | Encounters | POST /encounters (via stored proc), POST /encounters/{id}/close |
| 8 | SOAP Notes | GET/PATCH /encounters/{id}/soap |
| 9 | Vitals | POST/GET /encounters/{id}/vitals (BMI + abnormal auto by trigger) |
| 10 | Diagnoses | GET/POST/DELETE /encounters/{id}/diagnoses |
| 11 | Prescriptions | POST /encounters/{id}/prescriptions (409 on allergy conflict), PATCH /prescriptions/{id} (discontinue/reactivate) |
| 12 | Lab | Templates, orders, results, status update, abnormal flag |
| 13 | Imaging | Create/list/get/update imaging records, encounter-scoped + global |
| 14 | Referrals | Create/list/get + status transitions (pending→accepted→completed) |
| 15 | Care Plans | Create/list/get/update, blocks updates on completed/cancelled |
| 16 | Audit Logs | GET /audit-logs with filters (read-only, system_admin only) |
| 17 | Appointment check-in | POST /appointments/{id}/check-in → status=checked_in |

---

## Remaining Modules (2)

### Module 18 — Lab/Vitals Trends (skipped for now)
- `GET /patients/{id}/vitals/trends` — cross-encounter vitals time series
- `GET /patients/{id}/lab-trends?test_code=CBC` — cross-encounter lab results for a specific test
- No new tables needed — read-only queries across existing vitals + lab_results
- Useful for chronic disease monitoring charts on the frontend

### Module 19 — Patient Portal
- Needs a `patient_accounts` bridge table first: user_id FK→users, patient_id FK→patients (links a portal login to a patient record)
- Endpoints: POST /portal/me/appointments (request appointment → status=pending), GET /portal/me/appointments, GET /portal/me/encounters, GET /portal/me/prescriptions, GET /portal/me/lab-orders, GET /portal/me/vitals
- Key constraint: every endpoint enforces ownership — patient can only see their own data (patient_id comes from JWT token, not from URL)
- Appointment request flow: patient requests (status=pending) → receptionist reviews via existing GET /appointments?status=pending → receptionist confirms + assigns doctor via PATCH /appointments/{id}

---

## 5 Planned AI Features (not yet implemented)

All use OpenAI GPT-4o-mini. No new DB tables needed. Human-in-the-loop rule: AI never writes to DB directly — only suggests, doctor confirms.

### 1. Auto-SOAP Scribe — POST /ai/soap-draft
Doctor types raw shorthand → AI extracts S/O/A/P fields + suggests ICD-10 code → doctor confirms → saved to clinical_notes + diagnoses.

### 2. Patient Clinical Briefing — GET /patients/{id}/ai-summary
When doctor opens patient profile → FastAPI queries last 3 vitals + last 5 diagnoses + active prescriptions → AI generates 3-sentence clinical summary → displayed at top of profile. NOT saved to DB.

### 3. Lab Result Plain English — GET /lab-orders/{id}/ai-explain
Patient views their lab results → AI explains each parameter in plain non-medical language → shown alongside clinical values. Patient portal only. NOT saved to DB.

### 4. AI Referral Letter Draft — POST /ai/referral-draft
Doctor initiates referral → AI fetches current SOAP note + medical history → drafts professional referral letter → pre-fills referral form → doctor edits and confirms → saved to referrals table.

### 5. Chronic Disease Trend Hunter — GET /patients/{id}/ai-trend-analysis
FastAPI queries last 6 months of vitals ordered by recorded_at (uses index) → Python computes per-field deltas (e.g. BP sys +15.6% over 6 months) → AI narrates clinical significance → returned with trend data for charting. NOT saved to DB. Showcases value of vitals index on (patient_id, recorded_at).

---

## Key Design Decisions

| Decision | Reason |
|---|---|
| MRN generated in Python (not DB) | More control over format PDMS-YYYY-NNNNN |
| UUIDs for all PKs | No sequential ID guessing, safe for distributed future |
| Stored proc for encounter creation | Atomically creates encounter + empty SOAP note + increments visit number in one ACID transaction |
| Stored proc for prescription | Allergy check needs to read allergies table and conditionally abort — can't do that cleanly in app layer alone |
| implicit_returning=False on triggered tables | SQL Server audit triggers conflict with SQLAlchemy's OUTPUT clause — this disables it |
| Denormalized fields on lab_orders/lab_results | test_name, parameter_name, unit, normal_range copied so results are readable without joining back to templates |
| Soft delete (is_removed) | Allergies and medical history are legally significant — hard delete not allowed in clinical systems |
| Three timestamp columns | recorded_at = when entered into system, event_date = when it actually happened (can differ), validated_at = when a senior clinician verified it |

---

## File Structure

```
PDMS_IT/
├── backend/
│   ├── .env                         ← DB connection string, JWT secret
│   ├── requirements.txt
│   └── app/
│       ├── main.py                  ← FastAPI app, all routers included
│       ├── config.py                ← pydantic-settings from .env
│       ├── database.py              ← SQLAlchemy engine + get_db + Base
│       ├── core/
│       │   └── security.py         ← bcrypt, JWT create/decode, get_current_user, require_permission
│       ├── models/                  ← SQLAlchemy ORM models (one file per domain)
│       │   ├── user.py, patient.py, appointment.py, encounter.py
│       │   ├── lab.py, imaging.py, prescription.py
│       │   ├── referral.py, care_plan.py, audit_log.py
│       ├── schemas/                 ← Pydantic request/response shapes
│       ├── services/                ← Business logic + DB queries
│       └── routers/                 ← HTTP endpoint definitions
├── database/
│   ├── 00_create_database.sql
│   ├── 01_rbac.sql                  ← roles, permissions, role_permissions, users
│   ├── 02_patients.sql              ← patients, medical_history, allergies, vaccinations
│   ├── 03_scheduling.sql            ← appointments
│   ├── 04_encounters.sql            ← encounters, clinical_notes, vitals, diagnoses
│   ├── 05_medications.sql           ← prescriptions
│   ├── 06_diagnostics.sql           ← lab_test_templates, lab_test_parameters, lab_orders, lab_results, imaging_records
│   ├── 07_care.sql                  ← referrals, care_plans
│   ├── 08_security.sql              ← audit_logs
│   ├── 09_indexes.sql               ← all performance indexes
│   ├── 10_triggers.sql              ← BMI calc, abnormal vitals, audit triggers
│   ├── 11_stored_procs.sql          ← usp_create_encounter, usp_record_prescription
│   ├── 12_seed.sql                  ← roles, permissions, role-permission assignments, lab templates
│   └── 13_test_data.sql             ← test users, patients, appointments, encounters
├── API_DOCUMENTATION.md             ← Full API docs for frontend developer
└── README.md                        ← Project overview with AI features described
```

---

## How to Run

```powershell
cd backend
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

DB setup: run SQL files 00→13 in SSMS in order.
Swagger: http://localhost:8000/docs

---

## What to Discuss With Another AI

- Module 18: Lab/vitals trends implementation (read-only cross-encounter queries)
- Module 19: Patient portal — patient_accounts bridge table design + ownership enforcement
- AI features: how to implement any of the 5 using OpenAI API in FastAPI
- Frontend: how to connect to the backend using the API_DOCUMENTATION.md
- Presentation demo scenarios: acute visit workflow + chronic disease follow-up workflow
