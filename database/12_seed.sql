USE pdms_db;
GO

-- ============================================================
-- SEED DATA
-- Run order: 12 — run after all tables, indexes, triggers, procs
--
-- Sections:
--   A) Roles (6)
--   B) Permissions (23)
--   C) Role → Permission assignments
--   D) Lab test templates (11)
--   E) Lab test parameters (CBC, EUCr, HbA1c, BMP, LFT, TFT,
--      LIPID, UA, STREP, COVID, FLU)
-- ============================================================


-- ============================================================
-- A. ROLES
-- ============================================================
IF NOT EXISTS (SELECT 1 FROM roles WHERE role_name = 'system_admin')
    INSERT INTO roles (role_name, description) VALUES
    ('system_admin',   'Full system access: user management, audit logs, configuration'),
    ('doctor',         'Clinical access: encounters, SOAP notes, diagnoses, prescriptions, lab orders'),
    ('nurse',          'Nursing access: vitals, clinical notes, vaccinations, patient view'),
    ('receptionist',   'Front desk: patient registration, appointment booking'),
    ('lab_technician', 'Lab access: view pending orders, upload results'),
    ('patient',        'Patient portal: view own records, book appointments');
GO


-- ============================================================
-- B. PERMISSIONS
-- ============================================================
IF NOT EXISTS (SELECT 1 FROM permissions WHERE permission_name = 'manage_users')
    INSERT INTO permissions (permission_name, module, action, description) VALUES
    -- Users & System
    ('manage_users',          'users',          'manage', 'Create, update, deactivate user accounts and assign roles'),
    ('view_audit_logs',       'audit',          'view',   'Read and filter system audit logs'),
    -- Patients
    ('create_patient',        'patients',       'create', 'Register a new patient'),
    ('view_patient_record',   'patients',       'view',   'View patient profile and history'),
    -- Appointments
    ('book_appointment',      'appointments',   'create', 'Book a new appointment'),
    ('cancel_appointment',    'appointments',   'update', 'Cancel or reschedule an appointment'),
    -- Encounters
    ('create_encounter',      'encounters',     'create', 'Open a new clinical encounter'),
    ('close_encounter',       'encounters',     'update', 'Close an open encounter'),
    -- Clinical notes
    ('write_clinical_notes',  'clinical_notes', 'write',  'Create or update SOAP notes'),
    -- Vitals
    ('record_vitals',         'vitals',         'create', 'Record patient vitals for an encounter'),
    -- Diagnoses
    ('record_diagnosis',      'diagnoses',      'create', 'Add ICD-10 diagnoses to an encounter'),
    -- Prescriptions
    ('issue_prescription',    'prescriptions',  'create', 'Issue a prescription (allergy check enforced)'),
    ('view_prescriptions',    'prescriptions',  'view',   'View patient prescriptions'),
    -- Lab
    ('order_lab_test',        'lab',            'create', 'Create a lab order for a patient'),
    ('view_lab_orders',       'lab',            'view',   'View pending and completed lab orders'),
    ('upload_lab_result',     'lab',            'upload', 'Upload lab results for a completed order'),
    ('view_lab_results',      'lab',            'view',   'View lab results'),
    -- Imaging
    ('record_imaging',        'imaging',        'create', 'Record an imaging study'),
    -- Referrals
    ('create_referral',       'referrals',      'create', 'Create a specialist referral'),
    -- Care plans
    ('manage_care_plans',     'care_plans',     'manage', 'Create and update chronic disease care plans'),
    -- Medical history & allergies
    ('view_medical_history',    'medical_history', 'view',   'View patient medical history and allergies'),
    ('manage_medical_history',  'medical_history', 'manage', 'Add/update medical history and allergies'),
    -- Vaccinations
    ('update_vaccinations',   'vaccinations',   'update', 'Record and update vaccination history');
GO


-- ============================================================
-- C. ROLE → PERMISSION ASSIGNMENTS
-- ============================================================

-- system_admin
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.role_id, p.permission_id
FROM roles r, permissions p
WHERE r.role_name = 'system_admin'
  AND p.permission_name IN (
      'manage_users', 'view_audit_logs', 'view_patient_record',
      'book_appointment', 'cancel_appointment'
  )
  AND NOT EXISTS (
      SELECT 1 FROM role_permissions rp
      WHERE rp.role_id = r.role_id AND rp.permission_id = p.permission_id
  );
GO

-- doctor
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.role_id, p.permission_id
FROM roles r, permissions p
WHERE r.role_name = 'doctor'
  AND p.permission_name IN (
      'view_patient_record', 'book_appointment', 'cancel_appointment',
      'create_encounter', 'close_encounter',
      'write_clinical_notes', 'record_vitals', 'record_diagnosis',
      'issue_prescription', 'view_prescriptions',
      'order_lab_test', 'view_lab_orders', 'view_lab_results',
      'record_imaging', 'create_referral', 'manage_care_plans',
      'view_medical_history', 'manage_medical_history', 'update_vaccinations'
  )
  AND NOT EXISTS (
      SELECT 1 FROM role_permissions rp
      WHERE rp.role_id = r.role_id AND rp.permission_id = p.permission_id
  );
GO

-- nurse
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.role_id, p.permission_id
FROM roles r, permissions p
WHERE r.role_name = 'nurse'
  AND p.permission_name IN (
      'view_patient_record', 'record_vitals', 'write_clinical_notes',
      'view_lab_results', 'view_prescriptions',
      'view_medical_history', 'update_vaccinations'
  )
  AND NOT EXISTS (
      SELECT 1 FROM role_permissions rp
      WHERE rp.role_id = r.role_id AND rp.permission_id = p.permission_id
  );
GO

-- receptionist
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.role_id, p.permission_id
FROM roles r, permissions p
WHERE r.role_name = 'receptionist'
  AND p.permission_name IN (
      'create_patient', 'view_patient_record',
      'book_appointment', 'cancel_appointment'
  )
  AND NOT EXISTS (
      SELECT 1 FROM role_permissions rp
      WHERE rp.role_id = r.role_id AND rp.permission_id = p.permission_id
  );
GO

-- lab_technician
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.role_id, p.permission_id
FROM roles r, permissions p
WHERE r.role_name = 'lab_technician'
  AND p.permission_name IN (
      'view_patient_record', 'view_lab_orders',
      'upload_lab_result', 'view_lab_results'
  )
  AND NOT EXISTS (
      SELECT 1 FROM role_permissions rp
      WHERE rp.role_id = r.role_id AND rp.permission_id = p.permission_id
  );
GO

-- patient
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.role_id, p.permission_id
FROM roles r, permissions p
WHERE r.role_name = 'patient'
  AND p.permission_name IN (
      'view_patient_record', 'book_appointment', 'cancel_appointment',
      'view_prescriptions', 'view_lab_results'
  )
  AND NOT EXISTS (
      SELECT 1 FROM role_permissions rp
      WHERE rp.role_id = r.role_id AND rp.permission_id = p.permission_id
  );
GO


-- ============================================================
-- D. LAB TEST TEMPLATES
-- ============================================================
IF NOT EXISTS (SELECT 1 FROM lab_test_templates WHERE test_code = 'CBC')
    INSERT INTO lab_test_templates (test_name, test_code, test_category) VALUES
    ('Complete Blood Count',         'CBC',   'hematology'),
    ('Basic Metabolic Panel',        'BMP',   'biochemistry'),
    ('Electrolytes Urea Creatinine', 'EUCr',  'biochemistry'),
    ('Lipid Profile',                'LIPID', 'biochemistry'),
    ('Liver Function Test',          'LFT',   'biochemistry'),
    ('Thyroid Function Test',        'TFT',   'biochemistry'),
    ('Hemoglobin A1c',               'HbA1c', 'biochemistry'),
    ('Urinalysis',                   'UA',    'urinalysis'),
    ('Rapid Streptococcal Antigen',  'STREP', 'serology'),
    ('COVID-19 Rapid Antigen',       'COVID', 'serology'),
    ('Rapid Influenza Antigen',      'FLU',   'serology');
GO


-- ============================================================
-- E. LAB TEST PARAMETERS
-- Each block: DECLARE template id → INSERT parameters
-- All in separate batches (separated by GO) — this is correct
-- because each DECLARE uses a different variable name.
-- ============================================================

-- CBC Parameters
DECLARE @cbc_id UNIQUEIDENTIFIER = (SELECT template_id FROM lab_test_templates WHERE test_code = 'CBC');
IF NOT EXISTS (SELECT 1 FROM lab_test_parameters WHERE template_id = @cbc_id)
INSERT INTO lab_test_parameters
    (template_id, parameter_name, display_order, unit, normal_range_min, normal_range_max, normal_range_text, value_type)
VALUES
(@cbc_id, 'Hemoglobin',          1,  'g/dL',      12.0,  17.5,  NULL,      'numeric'),
(@cbc_id, 'PCV (Hematocrit)',     2,  '%',          37.0,  47.0,  NULL,      'numeric'),
(@cbc_id, 'MCV',                  3,  'fL',         80.0,  100.0, NULL,      'numeric'),
(@cbc_id, 'MCH',                  4,  'pg',         27.0,  33.0,  NULL,      'numeric'),
(@cbc_id, 'MCHC',                 5,  'g/dL',       32.0,  36.0,  NULL,      'numeric'),
(@cbc_id, 'White Blood Cells',    6,  'x10⁹/L',     4.5,   11.0,  NULL,      'numeric'),
(@cbc_id, 'Platelets',            7,  'x10⁹/L',     150.0, 400.0, NULL,      'numeric'),
(@cbc_id, 'Neutrophils',          8,  '%',          50.0,  70.0,  NULL,      'numeric'),
(@cbc_id, 'Lymphocytes',          9,  '%',          20.0,  40.0,  NULL,      'numeric'),
(@cbc_id, 'Monocytes',           10,  '%',           2.0,   8.0,  NULL,      'numeric');
GO

-- EUCr Parameters
DECLARE @eucr_id UNIQUEIDENTIFIER = (SELECT template_id FROM lab_test_templates WHERE test_code = 'EUCr');
IF NOT EXISTS (SELECT 1 FROM lab_test_parameters WHERE template_id = @eucr_id)
INSERT INTO lab_test_parameters
    (template_id, parameter_name, display_order, unit, normal_range_min, normal_range_max, normal_range_text, value_type)
VALUES
(@eucr_id, 'Sodium (Na+)',        1, 'mEq/L',   136.0, 145.0, NULL,          'numeric'),
(@eucr_id, 'Potassium (K+)',      2, 'mEq/L',     3.5,   5.0, NULL,          'numeric'),
(@eucr_id, 'Chloride (Cl-)',      3, 'mEq/L',    98.0, 107.0, NULL,          'numeric'),
(@eucr_id, 'Bicarbonate (HCO3-)', 4, 'mEq/L',    22.0,  29.0, NULL,          'numeric'),
(@eucr_id, 'Urea',                5, 'mmol/L',    2.5,   7.1, NULL,          'numeric'),
(@eucr_id, 'Creatinine',          6, 'µmol/L',   62.0, 106.0, NULL,          'numeric'),
(@eucr_id, 'eGFR',                7, 'mL/min',   60.0,  NULL, 'Above 60',    'numeric');
GO

-- HbA1c Parameters
DECLARE @hba1c_id UNIQUEIDENTIFIER = (SELECT template_id FROM lab_test_templates WHERE test_code = 'HbA1c');
IF NOT EXISTS (SELECT 1 FROM lab_test_parameters WHERE template_id = @hba1c_id)
INSERT INTO lab_test_parameters
    (template_id, parameter_name, display_order, unit, normal_range_min, normal_range_max, normal_range_text, value_type)
VALUES
(@hba1c_id, 'HbA1c', 1, '%', NULL, 5.7, 'Below 5.7%', 'numeric');
GO

-- BMP Parameters
DECLARE @bmp_id UNIQUEIDENTIFIER = (SELECT template_id FROM lab_test_templates WHERE test_code = 'BMP');
IF NOT EXISTS (SELECT 1 FROM lab_test_parameters WHERE template_id = @bmp_id)
INSERT INTO lab_test_parameters
    (template_id, parameter_name, display_order, unit, normal_range_min, normal_range_max, normal_range_text, value_type)
VALUES
(@bmp_id, 'Glucose (Fasting)', 1, 'mg/dL',   70.0,  99.0, NULL, 'numeric'),
(@bmp_id, 'Sodium (Na+)',       2, 'mEq/L',  136.0, 145.0, NULL, 'numeric'),
(@bmp_id, 'Potassium (K+)',     3, 'mEq/L',    3.5,   5.0, NULL, 'numeric'),
(@bmp_id, 'Chloride (Cl-)',     4, 'mEq/L',   98.0, 107.0, NULL, 'numeric'),
(@bmp_id, 'CO2 (Bicarbonate)',  5, 'mEq/L',   22.0,  29.0, NULL, 'numeric'),
(@bmp_id, 'BUN',                6, 'mg/dL',    7.0,  20.0, NULL, 'numeric'),
(@bmp_id, 'Creatinine',         7, 'mg/dL',    0.6,   1.2, NULL, 'numeric');
GO

-- LFT Parameters
DECLARE @lft_id UNIQUEIDENTIFIER = (SELECT template_id FROM lab_test_templates WHERE test_code = 'LFT');
IF NOT EXISTS (SELECT 1 FROM lab_test_parameters WHERE template_id = @lft_id)
INSERT INTO lab_test_parameters
    (template_id, parameter_name, display_order, unit, normal_range_min, normal_range_max, normal_range_text, value_type)
VALUES
(@lft_id, 'ALT (SGPT)',        1, 'U/L',    7.0,  40.0, NULL, 'numeric'),
(@lft_id, 'AST (SGOT)',        2, 'U/L',   10.0,  40.0, NULL, 'numeric'),
(@lft_id, 'ALP',               3, 'U/L',   44.0, 147.0, NULL, 'numeric'),
(@lft_id, 'GGT',               4, 'U/L',    9.0,  48.0, NULL, 'numeric'),
(@lft_id, 'Total Bilirubin',   5, 'mg/dL',  0.1,   1.2, NULL, 'numeric'),
(@lft_id, 'Direct Bilirubin',  6, 'mg/dL',  0.0,   0.3, NULL, 'numeric'),
(@lft_id, 'Total Protein',     7, 'g/dL',   6.0,   8.5, NULL, 'numeric'),
(@lft_id, 'Albumin',           8, 'g/dL',   3.5,   5.0, NULL, 'numeric');
GO

-- TFT Parameters
DECLARE @tft_id UNIQUEIDENTIFIER = (SELECT template_id FROM lab_test_templates WHERE test_code = 'TFT');
IF NOT EXISTS (SELECT 1 FROM lab_test_parameters WHERE template_id = @tft_id)
INSERT INTO lab_test_parameters
    (template_id, parameter_name, display_order, unit, normal_range_min, normal_range_max, normal_range_text, value_type)
VALUES
(@tft_id, 'TSH',     1, 'µIU/mL', 0.4,  4.0, NULL, 'numeric'),
(@tft_id, 'Free T4', 2, 'ng/dL',  0.8,  1.8, NULL, 'numeric'),
(@tft_id, 'Free T3', 3, 'pg/mL',  2.3,  4.2, NULL, 'numeric');
GO

-- Lipid Profile Parameters
DECLARE @lipid_id UNIQUEIDENTIFIER = (SELECT template_id FROM lab_test_templates WHERE test_code = 'LIPID');
IF NOT EXISTS (SELECT 1 FROM lab_test_parameters WHERE template_id = @lipid_id)
INSERT INTO lab_test_parameters
    (template_id, parameter_name, display_order, unit, normal_range_min, normal_range_max, normal_range_text, value_type)
VALUES
(@lipid_id, 'Total Cholesterol',   1, 'mg/dL', NULL, 200.0, 'Below 200',  'numeric'),
(@lipid_id, 'LDL Cholesterol',     2, 'mg/dL', NULL, 100.0, 'Below 100',  'numeric'),
(@lipid_id, 'HDL Cholesterol',     3, 'mg/dL', 40.0,  NULL, 'Above 40',   'numeric'),
(@lipid_id, 'Triglycerides',       4, 'mg/dL', NULL, 150.0, 'Below 150',  'numeric'),
(@lipid_id, 'Non-HDL Cholesterol', 5, 'mg/dL', NULL, 130.0, 'Below 130',  'numeric');
GO

-- Urinalysis Parameters
DECLARE @ua_id UNIQUEIDENTIFIER = (SELECT template_id FROM lab_test_templates WHERE test_code = 'UA');
IF NOT EXISTS (SELECT 1 FROM lab_test_parameters WHERE template_id = @ua_id)
INSERT INTO lab_test_parameters
    (template_id, parameter_name, display_order, unit, normal_range_min, normal_range_max, normal_range_text, value_type)
VALUES
(@ua_id, 'Color',               1,  '-',    NULL, NULL, 'Yellow/Pale Yellow', 'text'),
(@ua_id, 'Clarity',             2,  '-',    NULL, NULL, 'Clear',              'text'),
(@ua_id, 'pH',                  3,  '-',     4.5,  8.0, NULL,                 'numeric'),
(@ua_id, 'Specific Gravity',    4,  '-',   1.001, 1.035, NULL,                'numeric'),
(@ua_id, 'Protein',             5,  '-',    NULL, NULL, 'Negative',           'positive_negative'),
(@ua_id, 'Glucose',             6,  '-',    NULL, NULL, 'Negative',           'positive_negative'),
(@ua_id, 'Ketones',             7,  '-',    NULL, NULL, 'Negative',           'positive_negative'),
(@ua_id, 'Blood',               8,  '-',    NULL, NULL, 'Negative',           'positive_negative'),
(@ua_id, 'Leukocyte Esterase',  9,  '-',    NULL, NULL, 'Negative',           'positive_negative'),
(@ua_id, 'Nitrites',           10,  '-',    NULL, NULL, 'Negative',           'positive_negative');
GO

-- Rapid Strep Parameters
DECLARE @strep_id UNIQUEIDENTIFIER = (SELECT template_id FROM lab_test_templates WHERE test_code = 'STREP');
IF NOT EXISTS (SELECT 1 FROM lab_test_parameters WHERE template_id = @strep_id)
INSERT INTO lab_test_parameters
    (template_id, parameter_name, display_order, unit, normal_range_text, value_type)
VALUES
(@strep_id, 'Strep A Antigen', 1, '-', 'Negative', 'positive_negative');
GO

-- COVID-19 Parameters
DECLARE @covid_id UNIQUEIDENTIFIER = (SELECT template_id FROM lab_test_templates WHERE test_code = 'COVID');
IF NOT EXISTS (SELECT 1 FROM lab_test_parameters WHERE template_id = @covid_id)
INSERT INTO lab_test_parameters
    (template_id, parameter_name, display_order, unit, normal_range_text, value_type)
VALUES
(@covid_id, 'COVID-19 Antigen', 1, '-', 'Negative', 'positive_negative');
GO

-- Influenza Parameters
DECLARE @flu_id UNIQUEIDENTIFIER = (SELECT template_id FROM lab_test_templates WHERE test_code = 'FLU');
IF NOT EXISTS (SELECT 1 FROM lab_test_parameters WHERE template_id = @flu_id)
INSERT INTO lab_test_parameters
    (template_id, parameter_name, display_order, unit, normal_range_text, value_type)
VALUES
(@flu_id, 'Influenza A', 1, '-', 'Negative', 'positive_negative'),
(@flu_id, 'Influenza B', 2, '-', 'Negative', 'positive_negative');
GO

PRINT 'Seed data inserted successfully.';
PRINT 'Summary: 6 roles, 23 permissions, role-permission mappings, 11 lab templates + all parameters.';
GO
