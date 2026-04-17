# PDMS Backend API Documentation
**For Frontend Developers**

---

## Overview

| Item | Value |
|---|---|
| Base URL | `http://localhost:8000` |
| API Format | REST / JSON |
| Auth | JWT Bearer Token |
| Interactive Docs | `http://localhost:8000/docs` (Swagger UI — try all endpoints here) |

---

## How Authentication Works

### 1. Login to get tokens

```
POST /auth/login
Content-Type: application/x-www-form-urlencoded

username=admin&password=Admin@123
```

> **Important:** Login uses form-encoded body (not JSON) because of Swagger compatibility.

**Response:**
```json
{
  "access_token": "eyJhbGci...",
  "refresh_token": "eyJhbGci...",
  "token_type": "bearer",
  "user": {
    "user_id": "uuid",
    "username": "admin",
    "email": "admin@clinic.local",
    "role": "system_admin",
    "first_name": "System",
    "last_name": "Admin"
  }
}
```

### 2. Send token with every request

```
GET /patients
Authorization: Bearer eyJhbGci...
```

### 3. Refresh when token expires

```
POST /auth/refresh
Content-Type: application/json

{ "refresh_token": "eyJhbGci..." }
```

**Response:** new `access_token` + `refresh_token`

---

## TypeScript Helper (copy this)

```typescript
const BASE_URL = "http://localhost:8000";

// Store tokens after login
let accessToken = localStorage.getItem("access_token") ?? "";

async function apiFetch(path: string, options: RequestInit = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${accessToken}`,
      ...options.headers,
    },
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail ?? "Request failed");
  }
  return res.json();
}

// Login (form-encoded, not JSON)
async function login(username: string, password: string) {
  const res = await fetch(`${BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({ username, password }),
  });
  const data = await res.json();
  accessToken = data.access_token;
  localStorage.setItem("access_token", data.access_token);
  localStorage.setItem("refresh_token", data.refresh_token);
  return data;
}
```

---

## Common Response Patterns

| HTTP Code | Meaning |
|---|---|
| `200` | Success (GET, PATCH) |
| `201` | Created (POST) |
| `204` | Deleted (no body) |
| `400` | Bad request / validation error |
| `401` | Not logged in |
| `403` | Logged in but no permission |
| `404` | Resource not found |
| `409` | Conflict (e.g. allergy conflict on prescription) |

**Error shape:**
```json
{ "detail": "Patient not found" }
```

---

## Roles & Permissions

Roles seeded in the system:

| Role | Who |
|---|---|
| `system_admin` | IT admin — manages users |
| `doctor` | Creates encounters, prescriptions, orders labs |
| `nurse` | Records vitals, checks in patients |
| `receptionist` | Books appointments |
| `lab_technician` | Uploads lab results |
| `pharmacist` | Views/manages prescriptions |

> When a user doesn't have permission for an endpoint, the API returns `403 Forbidden`.

---

---

# Endpoints Reference

---

## AUTH

### POST /auth/login
Login and get JWT tokens.

**Request** (`application/x-www-form-urlencoded`):
```
username=john&password=Secret123
```

**Response `200`:**
```json
{
  "access_token": "string",
  "refresh_token": "string",
  "token_type": "bearer",
  "user": {
    "user_id": "uuid",
    "username": "string",
    "email": "string",
    "role": "string",
    "first_name": "string",
    "last_name": "string"
  }
}
```

---

### POST /auth/refresh
Get a new token pair using a valid refresh token.

**Request:**
```json
{ "refresh_token": "string" }
```

**Response `200`:**
```json
{
  "access_token": "string",
  "refresh_token": "string",
  "token_type": "bearer"
}
```

---

---

## USERS
> Requires role: `system_admin`

### GET /users
List all users.

**Query params:** `skip` (int, default 0), `limit` (int, default 50)

**Response `200`:** Array of user objects.
```json
[
  {
    "user_id": "uuid",
    "username": "string",
    "email": "string",
    "role": { "role_id": "uuid", "role_name": "string" },
    "first_name": "string",
    "last_name": "string",
    "is_active": true,
    "created_at": "datetime",
    "last_login": "datetime | null"
  }
]
```

---

### POST /users
Create a new user (staff account).

**Request:**
```json
{
  "username": "jsmith",
  "password": "SecurePass123",
  "email": "jsmith@clinic.local",
  "role_id": "uuid",
  "first_name": "John",
  "last_name": "Smith"
}
```

**Response `201`:** User object (same shape as GET).

---

### GET /users/roles
List all available roles (for user creation form dropdowns).

**Response `200`:**
```json
[
  { "role_id": "uuid", "role_name": "doctor" }
]
```

---

### GET /users/{user_id}
Get a single user by ID.

---

### PATCH /users/{user_id}
Update a user (all fields optional).

**Request:**
```json
{
  "email": "new@email.com",
  "role_id": "uuid",
  "first_name": "string",
  "last_name": "string",
  "is_active": true
}
```

---

### DELETE /users/{user_id}
Deactivate a user (soft delete — sets `is_active = false`).

---

---

## PATIENTS
> Requires permission: `view_patient_record` (read), `create_patient` (write)

### GET /patients
List/search patients.

**Query params:**
- `search` — searches first name, last name, MRN, phone
- `skip`, `limit`

**Response `200`:**
```json
[
  {
    "patient_id": "uuid",
    "mrn": "PDMS-2026-00001",
    "first_name": "string",
    "last_name": "string",
    "date_of_birth": "YYYY-MM-DD",
    "gender": "string | null",
    "blood_type": "string | null",
    "phone": "string | null",
    "email": "string | null",
    "address": "string | null",
    "emergency_contact_name": "string | null",
    "emergency_contact_phone": "string | null",
    "created_at": "datetime"
  }
]
```

---

### POST /patients
Register a new patient.

**Request:**
```json
{
  "first_name": "Jane",
  "last_name": "Doe",
  "date_of_birth": "1990-05-20",
  "gender": "female",
  "blood_type": "O+",
  "phone": "09123456789",
  "email": "jane@example.com",
  "address": "123 Main St",
  "emergency_contact_name": "John Doe",
  "emergency_contact_phone": "09987654321"
}
```

> MRN is auto-generated by the server (format: `PDMS-YYYY-NNNNN`).

**Response `201`:** Patient object.

---

### GET /patients/{patient_id}
Get a single patient.

---

### PATCH /patients/{patient_id}
Update patient demographics (all fields optional).

---

### GET /patients/{patient_id}/medical-history
List patient's background medical history.

---

### POST /patients/{patient_id}/medical-history
Add a medical history entry.

**Request:**
```json
{
  "condition_name": "Type 2 Diabetes",
  "icd_code": "E11",
  "onset_date": "2015-01-01",
  "is_chronic": true,
  "notes": "Managed with metformin"
}
```

---

### DELETE /patients/{patient_id}/medical-history/{history_id}
Soft-delete a medical history entry.

---

### GET /patients/{patient_id}/allergies
List patient allergies.

---

### POST /patients/{patient_id}/allergies
Add an allergy.

**Request:**
```json
{
  "allergen": "Penicillin",
  "reaction_type": "Anaphylaxis",
  "severity": "severe"
}
```
> `severity` values: `mild`, `moderate`, `severe`

---

### DELETE /patients/{patient_id}/allergies/{allergy_id}
Soft-delete an allergy.

---

### GET /patients/{patient_id}/vaccinations
List vaccinations.

---

### POST /patients/{patient_id}/vaccinations
Add a vaccination record.

**Request:**
```json
{
  "vaccine_name": "COVID-19 (Pfizer)",
  "dose_number": 2,
  "administered_at": "2024-03-15",
  "next_due_date": "2025-03-15",
  "notes": "No adverse reactions"
}
```

---

---

## APPOINTMENTS
> Requires permission: `book_appointment` (read/create), `cancel_appointment` (update/cancel)

### GET /appointments
List appointments with optional filters.

**Query params:**
- `patient_id` (uuid)
- `doctor_id` (uuid)
- `date` (YYYY-MM-DD string)
- `appt_status` — `scheduled` | `confirmed` | `checked_in` | `completed` | `cancelled`
- `skip`, `limit`

**Response `200`:**
```json
[
  {
    "appointment_id": "uuid",
    "patient_id": "uuid",
    "doctor_id": "uuid",
    "scheduled_at": "datetime",
    "reason": "string | null",
    "status": "scheduled",
    "notes": "string | null",
    "checked_at": "datetime | null",
    "created_by": "uuid",
    "created_at": "datetime"
  }
]
```

---

### POST /appointments
Book a new appointment.

**Request:**
```json
{
  "patient_id": "uuid",
  "doctor_id": "uuid",
  "scheduled_at": "2026-04-20T09:00:00",
  "reason": "Follow-up on blood pressure",
  "notes": null
}
```

---

### GET /appointments/{appointment_id}
Get a single appointment.

---

### PATCH /appointments/{appointment_id}
Reschedule or update status.

**Request (all optional):**
```json
{
  "scheduled_at": "2026-04-21T10:00:00",
  "reason": "updated reason",
  "notes": "updated notes",
  "status": "confirmed"
}
```

---

### DELETE /appointments/{appointment_id}
Cancel an appointment (sets status = `cancelled`).

---

### POST /appointments/{appointment_id}/check-in
Check a patient in on arrival (sets status = `checked_in`, records `checked_at`).

**No request body needed.**

---

---

## ENCOUNTERS
> Requires permission: `create_encounter`

### GET /encounters
List encounters with optional filters.

**Query params:** `patient_id`, `doctor_id`, `enc_status` (`open`|`closed`), `skip`, `limit`

**Response `200`:**
```json
[
  {
    "encounter_id": "uuid",
    "patient_id": "uuid",
    "doctor_id": "uuid",
    "appointment_id": "uuid | null",
    "encounter_date": "datetime",
    "encounter_type": "outpatient",
    "chief_complaint": "string | null",
    "status": "open",
    "visit_number": 1,
    "created_at": "datetime",
    "closed_at": "datetime | null"
  }
]
```

---

### POST /encounters
Open a new encounter.

**Request:**
```json
{
  "patient_id": "uuid",
  "doctor_id": "uuid",
  "appointment_id": "uuid",
  "encounter_type": "outpatient",
  "chief_complaint": "Chest pain since yesterday"
}
```
> `encounter_type` values: `outpatient`, `follow-up`, `emergency`
> `appointment_id` is optional (omit for walk-in)

---

### GET /encounters/{encounter_id}
Get a single encounter.

---

### POST /encounters/{encounter_id}/close
Close an encounter (no request body).

---

### GET /encounters/{encounter_id}/soap
Get the SOAP note for an encounter.

**Response `200`:**
```json
{
  "note_id": "uuid",
  "encounter_id": "uuid",
  "doctor_id": "uuid",
  "subjective": "string | null",
  "objective": "string | null",
  "assessment": "string | null",
  "plan": "string | null",
  "recorded_at": "datetime",
  "updated_at": "datetime | null"
}
```

---

### PATCH /encounters/{encounter_id}/soap
Update the SOAP note (all fields optional).

**Request:**
```json
{
  "subjective": "Patient reports chest pain",
  "objective": "BP 140/90, HR 88",
  "assessment": "Hypertension",
  "plan": "Increase lisinopril dose"
}
```

---

### POST /encounters/{encounter_id}/vitals
Record vitals for an encounter.

**Request (all fields optional — send what you have):**
```json
{
  "blood_pressure_sys": 120,
  "blood_pressure_dia": 80,
  "heart_rate": 72,
  "temperature": 36.8,
  "weight_kg": 68.5,
  "height_cm": 170.0,
  "oxygen_saturation": 98,
  "respiratory_rate": 16
}
```
> `bmi` and `is_abnormal` are auto-calculated by the database — do not send them.

---

### GET /encounters/{encounter_id}/vitals
List all vitals recorded for an encounter.

---

### POST /encounters/{encounter_id}/diagnoses
Add a diagnosis to an encounter.

**Request:**
```json
{
  "icd_code": "I10",
  "description": "Essential hypertension",
  "diagnosis_type": "primary",
  "condition": "confirmed",
  "timing": "chronic",
  "is_chronic": true
}
```
> `diagnosis_type`: `primary` | `secondary`
> `condition`: `suspected` | `confirmed` | `excluded` | `recurrent`
> `timing`: `acute` | `chronic` | `complication` | `recurrence`

---

### GET /encounters/{encounter_id}/diagnoses
List diagnoses for an encounter.

---

### DELETE /encounters/{encounter_id}/diagnoses/{diagnosis_id}
Remove a diagnosis (encounter must be open). Returns `204 No Content`.

---

---

## PRESCRIPTIONS
> Requires permission: `issue_prescription`

### POST /encounters/{encounter_id}/prescriptions
Issue a prescription for an encounter.

**Request:**
```json
{
  "patient_id": "uuid",
  "doctor_id": "uuid",
  "drug_name": "Lisinopril",
  "dosage": "10mg",
  "frequency": "Once daily",
  "duration": "30 days",
  "route": "oral",
  "instructions": "Take in the morning with water"
}
```
> `route` values: `oral`, `IV`, `topical`, `inhaled`, `subcutaneous`
> Returns `409` if the drug conflicts with a patient allergy.

---

### GET /encounters/{encounter_id}/prescriptions
List prescriptions for an encounter.

**Query params:** `active_only` (bool), `skip`, `limit`

---

### GET /prescriptions
List all prescriptions globally.

**Query params:** `patient_id`, `active_only`, `skip`, `limit`

---

### GET /prescriptions/{prescription_id}
Get a single prescription.

---

### PATCH /prescriptions/{prescription_id}
Discontinue or reactivate a prescription.

**Request:**
```json
{ "is_active": false }
```

---

---

## LAB

### GET /lab/templates
List all lab test templates (catalogue of available tests).

**Query params:** `active_only` (bool, default true)

**Response `200`:**
```json
[
  {
    "template_id": "uuid",
    "test_name": "Complete Blood Count",
    "test_code": "CBC",
    "test_category": "hematology",
    "description": "string | null",
    "is_active": true
  }
]
```

---

### GET /lab/templates/{template_id}
Get a template with its parameters (use this to build the result form).

**Response `200`:**
```json
{
  "template_id": "uuid",
  "test_name": "CBC",
  "test_code": "CBC",
  "test_category": "hematology",
  "parameters": [
    {
      "parameter_id": "uuid",
      "parameter_name": "Haemoglobin",
      "display_order": 1,
      "unit": "g/dL",
      "normal_range_min": 12.0,
      "normal_range_max": 17.5,
      "normal_range_text": null,
      "value_type": "numeric",
      "is_required": true
    }
  ]
}
```

---

### POST /encounters/{encounter_id}/lab-orders
Order a lab test for an encounter.

**Request:**
```json
{
  "template_id": "uuid",
  "test_name": "Complete Blood Count",
  "test_code": "CBC",
  "test_category": "hematology",
  "priority": "routine"
}
```
> `priority`: `routine` | `urgent` | `stat`

---

### GET /encounters/{encounter_id}/lab-orders
List lab orders for an encounter.

**Query params:** `order_status`, `skip`, `limit`

---

### GET /lab-orders
List all lab orders globally.

**Query params:** `patient_id`, `order_status`, `skip`, `limit`

---

### GET /lab-orders/{order_id}
Get a single lab order.

---

### PATCH /lab-orders/{order_id}/status
Update lab order status (used by lab technician).

**Request:**
```json
{ "status": "in-progress" }
```
> `status` values: `ordered` → `in-progress` → `completed`

---

### POST /lab-orders/{order_id}/results
Submit lab results (one entry per parameter).

**Request:**
```json
{
  "results": [
    {
      "parameter_id": "uuid",
      "parameter_name": "Haemoglobin",
      "result_value": "14.5",
      "unit": "g/dL",
      "normal_range": "12.0 - 17.5",
      "notes": null
    }
  ]
}
```
> `is_abnormal` and `abnormal_level` are auto-calculated by the server.

---

### GET /lab-orders/{order_id}/results
List results for a lab order.

**Response `200`:**
```json
[
  {
    "result_id": "uuid",
    "order_id": "uuid",
    "patient_id": "uuid",
    "parameter_name": "Haemoglobin",
    "result_value": "14.5",
    "unit": "g/dL",
    "normal_range": "12.0 - 17.5",
    "is_abnormal": false,
    "abnormal_level": null,
    "notes": null,
    "resulted_at": "datetime"
  }
]
```

---

---

## IMAGING
> Requires permission: `record_imaging`

### POST /encounters/{encounter_id}/imaging
Create an imaging record for an encounter.

**Request:**
```json
{
  "imaging_type": "X-ray",
  "body_part": "Chest",
  "findings": "No consolidation seen",
  "image_url": "https://storage.example.com/xray123.jpg",
  "radiologist_notes": "Normal chest X-ray"
}
```
> `imaging_type` values: `X-ray`, `Ultrasound`, `MRI`, `CT`, `ECG`

---

### GET /encounters/{encounter_id}/imaging
List imaging records for an encounter.

**Query params:** `imaging_type`, `skip`, `limit`

---

### GET /imaging
List all imaging records globally.

**Query params:** `patient_id`, `imaging_type`, `skip`, `limit`

---

### GET /imaging/{imaging_id}
Get a single imaging record.

---

### PATCH /imaging/{imaging_id}
Update an imaging record (radiologist fills in findings after the fact).

**Request (all optional):**
```json
{
  "findings": "Mild cardiomegaly",
  "radiologist_notes": "Updated after review",
  "image_url": "https://storage.example.com/updated.jpg"
}
```

---

---

## REFERRALS
> Requires permission: `create_referral`

### POST /encounters/{encounter_id}/referrals
Create a referral from an encounter.

**Request:**
```json
{
  "specialty": "Cardiology",
  "reason": "Persistent chest pain with abnormal ECG",
  "urgency": "urgent"
}
```
> `urgency` values: `routine` | `urgent`

---

### GET /encounters/{encounter_id}/referrals
List referrals for an encounter.

---

### GET /referrals
List all referrals globally.

**Query params:** `patient_id`, `ref_status`, `skip`, `limit`

---

### GET /referrals/{referral_id}
Get a single referral.

---

### PATCH /referrals/{referral_id}/status
Update referral status.

**Request:**
```json
{ "status": "accepted" }
```
> `status` flow: `pending` → `accepted` → `completed`

---

---

## CARE PLANS
> Requires permission: `manage_care_plans`

### POST /care-plans
Create a care plan for a patient.

**Request:**
```json
{
  "patient_id": "uuid",
  "condition": "Type 2 Diabetes",
  "goals": "Reduce HbA1c below 7%",
  "interventions": "Diet modification, Metformin 500mg BD",
  "start_date": "2026-04-17",
  "review_date": "2026-07-17",
  "notes": "Patient motivated to change diet"
}
```

---

### GET /care-plans
List care plans with filters.

**Query params:** `patient_id`, `doctor_id`, `plan_status`, `skip`, `limit`

---

### GET /care-plans/{plan_id}
Get a single care plan.

---

### PATCH /care-plans/{plan_id}
Update a care plan (blocked if status is `completed` or `cancelled`).

**Request (all optional):**
```json
{
  "goals": "updated goals",
  "interventions": "updated interventions",
  "review_date": "2026-10-17",
  "notes": "Patient doing well",
  "status": "completed"
}
```
> `status` values: `active` | `completed` | `cancelled`

---

---

## AUDIT LOGS
> Requires role: `system_admin`

### GET /audit-logs
View system audit trail (read-only, insert-only table).

**Query params:**
- `user_id` (uuid)
- `action` — `CREATE` | `UPDATE` | `DELETE` | `VIEW`
- `table_affected` (string, e.g. `patients`)
- `record_id` (uuid)
- `date_from`, `date_to` (ISO datetime)
- `skip`, `limit` (default 100)

**Response `200`:**
```json
[
  {
    "log_id": "uuid",
    "user_id": "uuid | null",
    "action": "CREATE",
    "module": "patients",
    "table_affected": "patients",
    "record_id": "uuid | null",
    "old_value": null,
    "new_value": "{\"first_name\":\"Jane\"}",
    "ip_address": "127.0.0.1",
    "user_agent": "string | null",
    "timestamp": "datetime"
  }
]
```

---

---

## Health Check

### GET /health
Check if backend and database are running. No auth required.

**Response `200`:**
```json
{
  "status": "ok",
  "database": "connected",
  "debug": false
}
```

---

---

## Typical Frontend Workflow Examples

### Workflow 1: Doctor opens a visit

```
1. GET /patients?search=Jane          → find patient
2. GET /appointments?patient_id=...   → check upcoming appointment
3. POST /appointments/{id}/check-in   → check patient in
4. POST /encounters                   → open encounter
5. POST /encounters/{id}/vitals       → nurse records vitals
6. PATCH /encounters/{id}/soap        → doctor fills SOAP note
7. POST /encounters/{id}/diagnoses    → add diagnosis
8. POST /encounters/{id}/prescriptions→ issue prescription
9. POST /encounters/{id}/close        → close encounter
```

### Workflow 2: Lab test flow

```
1. GET /lab/templates                         → show test catalogue
2. GET /lab/templates/{id}                    → get parameters for the form
3. POST /encounters/{id}/lab-orders           → doctor orders test
4. PATCH /lab-orders/{id}/status (in-progress)→ lab tech starts
5. POST /lab-orders/{id}/results              → lab tech submits results
6. PATCH /lab-orders/{id}/status (completed)  → mark complete
7. GET /lab-orders/{id}/results               → doctor views results
```

### Workflow 3: Appointment booking

```
1. GET /patients?search=...           → find patient
2. GET /users?role=doctor             → list doctors (use GET /users, filter by role on frontend)
3. POST /appointments                 → book appointment
4. PATCH /appointments/{id}           → reschedule if needed
```

---

## Notes for Frontend Developer

- All IDs are **UUIDs** (strings like `"550e8400-e29b-41d4-a716-446655440000"`)
- All datetimes are **ISO 8601** format: `"2026-04-17T09:30:00"`
- All dates (no time) are `"YYYY-MM-DD"` format
- `null` fields are optional — don't send them if empty, or send `null`
- Pagination: use `skip` and `limit` on all list endpoints (default limit is usually 50)
- The token expires — catch `401` responses and call `/auth/refresh` automatically
- CORS is not yet configured — ask the backend developer to add your frontend origin to the allowed list before deploying
