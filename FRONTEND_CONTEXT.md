# PDMS — Frontend Build Context
**Patient Data Management System | Outpatient Clinic | April 2026**

---

## What You Are Building

A role-based web frontend for an outpatient GP clinic system. Backend is already fully built (Python FastAPI + SQL Server). Your job is to build the HTML/CSS/TypeScript frontend that talks to it via REST/JSON.

**NOT** a hospital system. No inpatient, no billing, no pharmacy inventory.

---

## Tech Expectations

- Pure **HTML + CSS + TypeScript** (no React/Vue/Angular unless you prefer — vanilla is fine)
- Compile TypeScript to JS or use `<script type="module">` with a bundler
- All data from backend REST API at `http://localhost:8000`
- Auth via **JWT Bearer token** stored in `localStorage`
- Swagger UI available at `http://localhost:8000/docs` for testing

---

## 6 Roles — Build Role-Gated Views

| Role | What They Do |
|---|---|
| `system_admin` | Manage staff accounts, view audit logs |
| `doctor` | Encounters, SOAP notes, diagnoses, prescriptions, lab orders, referrals, care plans |
| `nurse` | Record vitals, view patient history, vaccinations |
| `receptionist` | Register patients, book/cancel/check-in appointments |
| `lab_technician` | View pending orders, upload results |
| `pharmacist` | View prescriptions |

After login, store `user.role` and show only the relevant nav/pages for that role.

---

## Auth

### Login (form-encoded, NOT JSON)
```
POST /auth/login
Content-Type: application/x-www-form-urlencoded
body: username=admin&password=Admin@123
```
Response:
```json
{
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "bearer",
  "user": { "user_id": "uuid", "username": "admin", "role": "system_admin", "first_name": "System", "last_name": "Admin" }
}
```
Store both tokens in `localStorage`. Send `Authorization: Bearer <access_token>` on every request.

### Refresh token
```
POST /auth/refresh
{ "refresh_token": "..." }
```
On 401 → auto-refresh → retry original request.

### TypeScript API helper
```typescript
const BASE = "http://localhost:8000";
let token = localStorage.getItem("access_token") ?? "";

async function api(path: string, opts: RequestInit = {}) {
  const res = await fetch(`${BASE}${path}`, {
    ...opts,
    headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}`, ...opts.headers }
  });
  if (res.status === 401) { /* refresh and retry */ }
  if (!res.ok) { const e = await res.json(); throw new Error(e.detail); }
  return res.status === 204 ? null : res.json();
}

async function login(username: string, password: string) {
  const res = await fetch(`${BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({ username, password })
  });
  const data = await res.json();
  token = data.access_token;
  localStorage.setItem("access_token", data.access_token);
  localStorage.setItem("refresh_token", data.refresh_token);
  localStorage.setItem("user", JSON.stringify(data.user));
  return data;
}
```

---

## HTTP Response Codes
| Code | Meaning |
|---|---|
| 200 | OK |
| 201 | Created |
| 204 | Deleted (no body) |
| 400 | Validation error |
| 401 | Not logged in |
| 403 | No permission |
| 404 | Not found |
| 409 | Conflict (e.g. allergy conflict on prescription) |

Error body: `{ "detail": "message" }`

---

## Data Types
- All IDs: **UUID strings** `"550e8400-..."`
- Datetimes: **ISO 8601** `"2026-04-17T09:30:00"`
- Dates only: `"YYYY-MM-DD"`
- Pagination: `?skip=0&limit=50` on all list endpoints

---

## Pages to Build (by role)

### All Roles
- **Login page** — username + password form → POST /auth/login

### Receptionist
- **Patient List** — search bar + table → GET /patients?search=
- **Register Patient** — form → POST /patients
- **Patient Profile** (view only) — GET /patients/{id}
- **Appointment List** — filter by date/doctor/status → GET /appointments
- **Book Appointment** — pick patient + doctor + datetime → POST /appointments
- **Appointment Detail** — reschedule (PATCH), cancel (DELETE), check-in (POST /check-in)

### Doctor
- **Dashboard** — today's appointments + open encounters
- **Patient Profile** — demographics + medical history + allergies + vaccinations (read)
- **Encounter List** for patient → GET /encounters?patient_id=
- **Open Encounter** → POST /encounters
- **Encounter Detail page** containing:
  - SOAP Note editor → GET/PATCH /encounters/{id}/soap
  - Vitals list → GET /encounters/{id}/vitals
  - Diagnoses list → GET/POST/DELETE /encounters/{id}/diagnoses
  - Prescriptions list → GET/POST /encounters/{id}/prescriptions (show 409 allergy conflict)
  - Lab Orders list → GET/POST /encounters/{id}/lab-orders
  - Imaging records → GET/POST /encounters/{id}/imaging
  - Referrals → GET/POST /encounters/{id}/referrals
  - Close Encounter button → POST /encounters/{id}/close
- **Care Plans** — list + create + update → GET/POST/PATCH /care-plans
- **Referrals** — list + status update → GET /referrals, PATCH /referrals/{id}/status

### Nurse
- **Patient Profile** (view only)
- **Record Vitals** — form inside encounter → POST /encounters/{id}/vitals
- **Vaccination Records** — GET/POST /patients/{id}/vaccinations

### Lab Technician
- **Pending Lab Orders** → GET /lab-orders?order_status=ordered
- **Order Detail** → GET /lab-orders/{id}, GET /lab/templates/{template_id} (to build result form)
- **Submit Results** → PATCH /lab-orders/{id}/status (in-progress), POST /lab-orders/{id}/results, PATCH status (completed)

### System Admin
- **User List** → GET /users
- **Create User** → GET /users/roles (for dropdown), POST /users
- **Edit/Deactivate User** → PATCH /users/{id}, DELETE /users/{id}
- **Audit Log Viewer** → GET /audit-logs with date/action/table filters

### Pharmacist
- **Prescriptions List** → GET /prescriptions?patient_id=
- **Discontinue/Reactivate** → PATCH /prescriptions/{id} `{ "is_active": false/true }`

---

## Full API Reference

### AUTH
```
POST  /auth/login         form-encoded: username, password
POST  /auth/refresh       { "refresh_token": "..." }
```

### USERS (system_admin only)
```
GET    /users             ?skip&limit
POST   /users             { username, password, email, role_id, first_name, last_name }
GET    /users/roles        returns [{ role_id, role_name }]
GET    /users/{id}
PATCH  /users/{id}        { email?, role_id?, first_name?, last_name?, is_active? }
DELETE /users/{id}        soft-deactivates
```

User object:
```json
{ "user_id":"uuid", "username":"str", "email":"str", "role":{"role_id":"uuid","role_name":"str"}, "first_name":"str", "last_name":"str", "is_active":true, "created_at":"dt", "last_login":"dt|null" }
```

### PATIENTS
```
GET    /patients              ?search&skip&limit
POST   /patients              { first_name, last_name, date_of_birth, gender?, blood_type?, phone?, email?, address?, emergency_contact_name?, emergency_contact_phone? }
GET    /patients/{id}
PATCH  /patients/{id}         all fields optional

GET    /patients/{id}/medical-history
POST   /patients/{id}/medical-history   { condition_name, icd_code?, onset_date?, is_chronic, notes? }
DELETE /patients/{id}/medical-history/{hid}

GET    /patients/{id}/allergies
POST   /patients/{id}/allergies         { allergen, reaction_type?, severity }  severity: mild|moderate|severe
DELETE /patients/{id}/allergies/{aid}

GET    /patients/{id}/vaccinations
POST   /patients/{id}/vaccinations      { vaccine_name, dose_number?, administered_at?, next_due_date?, notes? }
```

Patient object:
```json
{ "patient_id":"uuid", "mrn":"PDMS-2026-00001", "first_name":"str", "last_name":"str", "date_of_birth":"YYYY-MM-DD", "gender":"str|null", "blood_type":"str|null", "phone":"str|null", "email":"str|null", "address":"str|null", "emergency_contact_name":"str|null", "emergency_contact_phone":"str|null", "created_at":"dt" }
```

### APPOINTMENTS
```
GET    /appointments              ?patient_id&doctor_id&date&appt_status&skip&limit
                                   status values: scheduled|confirmed|checked_in|completed|cancelled
POST   /appointments              { patient_id, doctor_id, scheduled_at, reason?, notes? }
GET    /appointments/{id}
PATCH  /appointments/{id}         { scheduled_at?, reason?, notes?, status? }
DELETE /appointments/{id}         cancels
POST   /appointments/{id}/check-in  no body — sets status=checked_in
```

### ENCOUNTERS
```
GET    /encounters                ?patient_id&doctor_id&enc_status(open|closed)&skip&limit
POST   /encounters                { patient_id, doctor_id, appointment_id?(optional), encounter_type, chief_complaint? }
                                   encounter_type: outpatient|follow-up|emergency
GET    /encounters/{id}
POST   /encounters/{id}/close     no body

GET    /encounters/{id}/soap
PATCH  /encounters/{id}/soap      { subjective?, objective?, assessment?, plan? }

POST   /encounters/{id}/vitals    { blood_pressure_sys?, blood_pressure_dia?, heart_rate?, temperature?, weight_kg?, height_cm?, oxygen_saturation?, respiratory_rate? }
                                   bmi + is_abnormal AUTO by DB trigger — do not send
GET    /encounters/{id}/vitals

POST   /encounters/{id}/diagnoses { icd_code, description, diagnosis_type, condition, timing, is_chronic }
                                   diagnosis_type: primary|secondary
                                   condition: suspected|confirmed|excluded|recurrent
                                   timing: acute|chronic|complication|recurrence
GET    /encounters/{id}/diagnoses
DELETE /encounters/{id}/diagnoses/{did}  returns 204
```

Encounter object:
```json
{ "encounter_id":"uuid", "patient_id":"uuid", "doctor_id":"uuid", "appointment_id":"uuid|null", "encounter_date":"dt", "encounter_type":"outpatient", "chief_complaint":"str|null", "status":"open", "visit_number":1, "created_at":"dt", "closed_at":"dt|null" }
```

SOAP object:
```json
{ "note_id":"uuid", "encounter_id":"uuid", "doctor_id":"uuid", "subjective":"str|null", "objective":"str|null", "assessment":"str|null", "plan":"str|null", "recorded_at":"dt", "updated_at":"dt|null" }
```

Vitals object:
```json
{ "vital_id":"uuid", "blood_pressure_sys":120, "blood_pressure_dia":80, "heart_rate":72, "temperature":36.8, "weight_kg":68.5, "height_cm":170.0, "bmi":23.7, "oxygen_saturation":98, "respiratory_rate":16, "is_abnormal":false, "recorded_by":"uuid", "recorded_at":"dt" }
```

### PRESCRIPTIONS
```
POST   /encounters/{id}/prescriptions  { patient_id, doctor_id, drug_name, dosage, frequency, duration, route, instructions? }
                                        route: oral|IV|topical|inhaled|subcutaneous
                                        → 409 if drug name matches patient allergy
GET    /encounters/{id}/prescriptions  ?active_only&skip&limit
GET    /prescriptions                  ?patient_id&active_only&skip&limit
GET    /prescriptions/{id}
PATCH  /prescriptions/{id}             { is_active: false }  ← discontinue
```

Prescription object:
```json
{ "prescription_id":"uuid", "encounter_id":"uuid", "patient_id":"uuid", "doctor_id":"uuid", "drug_name":"str", "dosage":"str", "frequency":"str", "duration":"str", "route":"oral", "instructions":"str|null", "is_active":true, "prescribed_at":"dt" }
```

### LAB
```
GET    /lab/templates               ?active_only
GET    /lab/templates/{id}          includes parameters array (use to build result form)

POST   /encounters/{id}/lab-orders  { template_id?, test_name, test_code, test_category, priority }
                                     priority: routine|urgent|stat
GET    /encounters/{id}/lab-orders  ?order_status&skip&limit
GET    /lab-orders                  ?patient_id&order_status&skip&limit
GET    /lab-orders/{id}
PATCH  /lab-orders/{id}/status      { "status": "in-progress" }  ordered→in-progress→completed
POST   /lab-orders/{id}/results     { results: [{ parameter_id?, parameter_name, result_value, unit, normal_range, notes? }] }
GET    /lab-orders/{id}/results
```

Lab template with parameters:
```json
{ "template_id":"uuid", "test_name":"CBC", "test_code":"CBC", "test_category":"hematology", "parameters": [{ "parameter_id":"uuid", "parameter_name":"Haemoglobin", "unit":"g/dL", "normal_range_min":12.0, "normal_range_max":17.5, "value_type":"numeric", "display_order":1 }] }
```

Lab result object:
```json
{ "result_id":"uuid", "parameter_name":"Haemoglobin", "result_value":"14.5", "unit":"g/dL", "normal_range":"12.0 - 17.5", "is_abnormal":false, "abnormal_level":"low|borderline|high|critical|null", "resulted_at":"dt" }
```

### IMAGING
```
POST   /encounters/{id}/imaging    { imaging_type, body_part, findings?, image_url?, radiologist_notes? }
                                    imaging_type: X-ray|Ultrasound|MRI|CT|ECG
GET    /encounters/{id}/imaging    ?imaging_type&skip&limit
GET    /imaging                    ?patient_id&imaging_type&skip&limit
GET    /imaging/{id}
PATCH  /imaging/{id}               { findings?, radiologist_notes?, image_url? }
```

### REFERRALS
```
POST   /encounters/{id}/referrals  { specialty, reason, urgency }  urgency: routine|urgent
GET    /encounters/{id}/referrals
GET    /referrals                  ?patient_id&ref_status&skip&limit
GET    /referrals/{id}
PATCH  /referrals/{id}/status      { "status": "accepted" }  pending→accepted→completed
```

### CARE PLANS
```
POST   /care-plans                 { patient_id, condition, goals, interventions, start_date, review_date, notes? }
GET    /care-plans                 ?patient_id&doctor_id&plan_status&skip&limit
GET    /care-plans/{id}
PATCH  /care-plans/{id}            { goals?, interventions?, review_date?, notes?, status? }
                                    status: active|completed|cancelled
                                    blocked if already completed/cancelled
```

### AUDIT LOGS (system_admin only)
```
GET    /audit-logs    ?user_id&action(CREATE|UPDATE|DELETE|VIEW)&table_affected&record_id&date_from&date_to&skip&limit(default 100)
```
Audit log object:
```json
{ "log_id":"uuid", "user_id":"uuid|null", "action":"CREATE", "module":"patients", "table_affected":"patients", "record_id":"uuid|null", "old_value":"json_str|null", "new_value":"json_str|null", "ip_address":"str", "timestamp":"dt" }
```

### HEALTH CHECK
```
GET /health   (no auth) → { "status":"ok", "database":"connected" }
```

---

## UI Workflow Flows

### Acute Visit (doctor + receptionist + nurse + lab tech)
```
1. Receptionist: GET /patients?search= → find patient
2. Receptionist: POST /appointments → book appointment
3. Receptionist: POST /appointments/{id}/check-in → patient arrives
4. Nurse: POST /encounters/{id}/vitals → record BP, temp, weight etc
5. Doctor: POST /encounters → open encounter (linked to appointment)
6. Doctor: PATCH /encounters/{id}/soap → fill S/O/A/P
7. Doctor: POST /encounters/{id}/diagnoses → add ICD-10
8. Doctor: POST /encounters/{id}/prescriptions → issue drug (watch for 409)
9. Doctor: POST /encounters/{id}/lab-orders → order test
10. Lab Tech: PATCH /lab-orders/{id}/status (in-progress) → start processing
11. Lab Tech: POST /lab-orders/{id}/results → upload results
12. Lab Tech: PATCH /lab-orders/{id}/status (completed)
13. Doctor: GET /lab-orders/{id}/results → review, red-highlight is_abnormal
14. Doctor: POST /encounters/{id}/close → close encounter
```

### Chronic Disease Follow-up
```
1-4: Same as above
5. Doctor: GET /encounters?patient_id= → review previous encounters
6. Doctor: GET /care-plans?patient_id= → review care plan
7. Doctor: PATCH /encounters/{id}/soap → update SOAP
8. Doctor: POST /encounters/{id}/lab-orders → periodic labs
9. Doctor: PATCH /care-plans/{id} → update plan/goals
10. Doctor: POST /encounters/{id}/referrals (if complication)
11. Doctor: POST /encounters/{id}/close
```

---

## Key UI Rules

- **Allergy conflict (409)**: when prescribing shows red banner — "Drug conflicts with patient allergy: [allergen]. Confirm override?" — must be a deliberate re-submit decision.
- **Abnormal vitals / lab**: auto-flagged by backend — highlight `is_abnormal: true` rows in red/amber.
- **Encounter must be open** to add diagnoses/vitals/prescriptions/lab orders — show disabled state if encounter is closed.
- **Soft deletes**: allergies, medical history, prescriptions use `is_removed` — don't show them, just call DELETE which soft-removes.
- **MRN**: display prominently on patient profile — format `PDMS-2026-00001`.
- **Visit number**: show on each encounter — comes back as `visit_number` integer.
- **Date inputs**: send as `"YYYY-MM-DD"`, datetimes as `"YYYY-MM-DDTHH:MM:SS"`.

---

## Test Credentials (seeded in DB)

| Role | Username | Password |
|---|---|---|
| system_admin | admin | Admin@123 |
| doctor | dr_smith | Doctor@123 |
| nurse | nurse_amy | Nurse@123 |
| receptionist | reception1 | Reception@123 |
| lab_technician | labtech1 | LabTech@123 |

---

## CORS Note

Backend CORS is not yet configured. Add your frontend origin to the FastAPI CORS middleware in `backend/app/main.py`:
```python
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
```
