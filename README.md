# PDMS — Patient Data Management System

A secure, web-based clinical data management system designed for small to medium-sized outpatient primary healthcare clinics. The system manages patient data from initial registration through diagnosis, treatment, and long-term chronic disease monitoring.

> **University IT Project** · Focus: Software Architecture + Advanced Database Concepts · Timeline: 2 months

---

## Table of Contents

- [Overview](#overview)
- [System Roles](#system-roles)
- [Clinical Workflows](#clinical-workflows)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Database Design](#database-design)
- [Advanced Database Concepts](#advanced-database-concepts)
- [API Modules](#api-modules)
- [AI-Powered Features](#ai-powered-features)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)

---

## Overview

PDMS is **not** a full Hospital Management System. It is scoped specifically to outpatient clinic workflows:

**In Scope:**
- Patient registration and profile management
- Appointment scheduling with conflict detection
- Outpatient clinical encounters (acute and follow-up visits)
- SOAP format clinical notes
- ICD-10 diagnoses
- Vitals recording and trend tracking
- Prescriptions with allergy safety check
- Lab orders and dynamic results with abnormal flagging
- Basic imaging record keeping
- Allergy and vaccination management
- Referrals to external specialists
- Chronic disease care plans
- Role-based access control (RBAC)
- Full audit logging

**Out of Scope:** Inpatient wards, billing, pharmacy inventory, multi-branch networks, HL7/FHIR interoperability, patient portal, AI-assisted clinical tools (planned for future).

---

## System Roles

| Role | Key Responsibilities |
|------|---------------------|
| **System Admin** | Manage users, assign roles/permissions, view audit logs |
| **Doctor** | Encounters, SOAP notes, ICD-10 diagnoses, prescriptions, lab orders, referrals, care plans |
| **Nurse** | Record vitals, view patient history, update vaccination records |
| **Receptionist** | Register patients, book/cancel appointments |
| **Lab Technician** | View pending orders, upload results, flag abnormals |

---

## Clinical Workflows

### Workflow 1 — Acute Visit
*Cold, flu, injury, infection, one-time consultation*

```
Receptionist registers patient
    → Receptionist books appointment
    → Nurse records vitals on arrival
    → Doctor opens encounter (stored proc fires)
    → Doctor writes SOAP note
    → Doctor records ICD-10 diagnosis
    → Doctor issues prescription (allergy check runs)
    → Doctor orders lab test
    → Lab technician uploads result (abnormal flag set)
    → Doctor closes encounter
    → Patient views records via portal
```

### Workflow 2 — Chronic Disease Follow-up
*Diabetes, hypertension, asthma, ongoing conditions*

```
Receptionist books scheduled follow-up
    → Nurse records vitals (system shows previous values)
    → Doctor opens encounter
    → Doctor reviews previous encounters, lab trends, care plan
    → Doctor writes SOAP note
    → Doctor orders periodic labs (e.g. HbA1c)
    → Lab technician uploads results
    → Doctor updates care plan and prescriptions
    → Doctor creates referral if complication detected
    → Encounter closed, next follow-up scheduled
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.13, FastAPI |
| **ORM** | SQLAlchemy 2.0 |
| **Database** | Microsoft SQL Server (local: Windows Auth, production: SQL Server Auth on AWS EC2) |
| **Auth** | JWT (access + refresh tokens), bcrypt password hashing |
| **Caching** | Redis (patient summaries, RBAC lookups) |
| **Frontend** | HTML5, Vanilla JavaScript, CSS3 |

---

## Project Structure

```
PDMS_IT/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, router registration
│   │   ├── config.py            # Pydantic settings from .env
│   │   ├── database.py          # SQLAlchemy engine + get_db
│   │   ├── core/
│   │   │   └── security.py      # bcrypt, JWT, get_current_user, require_permission
│   │   ├── models/              # SQLAlchemy ORM models (one file per domain)
│   │   ├── schemas/             # Pydantic request/response shapes
│   │   ├── services/            # Business logic layer
│   │   └── routers/             # HTTP endpoints
│   ├── requirements.txt
│   └── .env
├── database/
│   ├── 00_create_database.sql
│   ├── 01_rbac.sql
│   ├── 02_patients.sql
│   ├── 03_scheduling.sql
│   ├── 04_encounters.sql
│   ├── 05_medications.sql
│   ├── 06_diagnostics.sql
│   ├── 07_care.sql
│   ├── 08_security.sql
│   ├── 09_indexes.sql
│   ├── 10_triggers.sql
│   ├── 11_stored_procs.sql
│   └── 12_seed.sql
└── Context.txt                  # Master project specification
```

### Request Flow

```
HTTP Request
    → routers/       (endpoint definition + permission guard)
    → services/      (business logic, DB queries)
    → models/        (SQLAlchemy ORM ↔ SQL Server)
    ↑
    schemas/         (validate input / shape output at router boundary)
    ↑
    core/security.py (JWT decoded → current user injected into every protected route)
```

---

## Database Design

20 normalised entities (3NF/BCNF) across 6 domain groups:

| Group | Tables |
|-------|--------|
| **RBAC** | users, roles, permissions, role_permissions |
| **Patient** | patients, medical_history, allergies, vaccinations |
| **Scheduling** | appointments |
| **Clinical Encounter** | encounters, clinical_notes, diagnoses, vitals |
| **Medication** | prescriptions |
| **Diagnostics** | lab_orders, lab_test_templates, lab_test_parameters, lab_results, imaging_records |
| **Care Coordination** | referrals, care_plans |
| **Security** | audit_logs |

**Key design decisions:**
- All PKs: `UNIQUEIDENTIFIER DEFAULT NEWID()`
- MRN format: `PDMS-YYYY-NNNNN` — generated in Python service layer
- Soft delete: `is_removed BIT` on allergies, medical_history, prescriptions
- Three timestamp fields: `recorded_at`, `event_date`, `validated_at`

---

## Advanced Database Concepts

| Concept | Implementation |
|---------|---------------|
| **Normalisation** | All 20 entities in 3NF/BCNF |
| **Indexing** | On `patient_id`, `encounter_date`, `doctor_id`, `is_abnormal`, `ordered_at`, `icd_code` |
| **Stored Procedures** | `usp_create_encounter` (ACID, auto visit number, empty SOAP shell), `usp_record_prescription` (allergy check) |
| **Triggers** | `trg_audit_*` on all clinical tables, `trg_calculate_bmi` on vitals, `trg_flag_abnormal_vitals` |
| **ACID Transactions** | All stored procs use `BEGIN TRY / COMMIT / ROLLBACK` |
| **JSON Storage** | `audit_logs.old_value` and `new_value` stored via `FOR JSON PATH` |
| **Full-Text Search** | FTS index on `clinical_notes` and `diagnoses` using `CONTAINS()` |
| **Soft Delete** | `is_removed` + `valid_from` + `valid_until` |
| **Redis Caching** | Patient summaries and RBAC permission lookups |

---

## API Modules

| # | Module | Endpoints | Key Features |
|---|--------|-----------|-------------|
| 1 | **Health** | `GET /health` | DB connectivity check |
| 2 | **Auth** | `POST /auth/login`, `POST /auth/refresh` | JWT access + refresh tokens |
| 3 | **Users** | `GET/POST/PATCH/DELETE /users` | Full user CRUD, role listing |
| 4 | **Patients** | `GET/POST/PATCH /patients` + sub-resources | MRN generation, medical history, allergies, vaccinations |
| 5 | **Appointments** | `GET/POST/PATCH/DELETE /appointments` | Conflict detection (±30 min window), status lifecycle |
| 6 | **Encounters** | `POST /encounters` | Calls `usp_create_encounter` stored proc, auto SOAP shell |
| 7 | **Vitals** | `POST /encounters/{id}/vitals` | BMI auto-calculated by trigger, abnormal flag by trigger |
| 8 | **Clinical Notes** | `GET/PATCH /encounters/{id}/notes` | SOAP format update |
| 9 | **Diagnoses** | `GET/POST /encounters/{id}/diagnoses` | ICD-10, primary/secondary, timing |
| 10 | **Prescriptions** | `POST /encounters/{id}/prescriptions` | Calls `usp_record_prescription`, allergy safety check |
| 11 | **Lab Orders** | `GET/POST /encounters/{id}/lab-orders` | Priority levels (routine/urgent/stat) |
| 12 | **Lab Results** | `POST /lab-orders/{id}/results` | Dynamic per-parameter results, abnormal flagging |
| 13 | **Imaging** | `GET/POST /encounters/{id}/imaging` | Type, findings, image URL |
| 14 | **Referrals** | `GET/POST /encounters/{id}/referrals` | Specialty, urgency, status lifecycle |
| 15 | **Care Plans** | `GET/POST/PATCH /patients/{id}/care-plans` | Chronic disease management |
| 16 | **Audit Logs** | `GET /audit-logs` | Read-only, filter by user/table/date |

---

## Getting Started

### Prerequisites
- Python 3.13+
- Microsoft SQL Server (local via SSMS)
- Redis (for caching)

### 1. Database Setup
Run all SQL files in SSMS in order:
```sql
-- Run in SSMS, in this exact order:
00_create_database.sql
01_rbac.sql
02_patients.sql
03_scheduling.sql
04_encounters.sql
05_medications.sql
06_diagnostics.sql
07_care.sql
08_security.sql
09_indexes.sql
10_triggers.sql
11_stored_procs.sql
12_seed.sql         -- seeds roles, permissions, and admin user
```

### 2. Backend Setup
```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. Run the Server
```powershell
uvicorn app.main:app --reload --port 8000
```

### 4. Swagger UI
Open **http://localhost:8000/docs** to explore and test all endpoints interactively.

---

## Environment Variables

Create `backend/.env`:

```env
DATABASE_URL=mssql+pyodbc://localhost/pdms_db?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes

SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

REDIS_URL=redis://localhost:6379

DEBUG=true
```

---

### AI-Powered Clinical Features
1. **Auto-SOAP Scribe** — AI-powered extraction of SOAP fields from raw clinical notes
2. **Patient Clinical Summary** — AI-generated 3-sentence clinical briefing from recent vitals, diagnoses, and prescriptions
3. **ICD_10 Code Suggestion** — AI-powered suggest ICD_Code based on the provided Symptoms


### Frontend
- Full React/Next.js frontend replacement for current vanilla JavaScript implementation
