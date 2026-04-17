USE pdms_db;
GO

-- ============================================================
-- TEST / DEMO DATA
-- Run order: 13 — run after 12_seed.sql
--
-- Users    : Admin, Dr. Aung Zaw Myo, Dr. Kay Thi Htun,
--            Su Lay Nwe (Nurse), Phyo Wai (Lab), May Thae (Receptionist)
-- Patients : Ko Min Thu, Ma Aye Aye, U Kyaw Zin, Daw Hla Hla
-- Clinical : 1 complete encounter with SOAP, vitals, diagnosis,
--            prescription (allergy-safe), CBC lab order + results
-- ============================================================


-- ============================================================
-- SECTION 1: USERS
-- ============================================================
PRINT '--- Inserting users ---';

DECLARE @role_admin  UNIQUEIDENTIFIER = (SELECT role_id FROM roles WHERE role_name = 'system_admin');
DECLARE @role_doctor UNIQUEIDENTIFIER = (SELECT role_id FROM roles WHERE role_name = 'doctor');
DECLARE @role_nurse  UNIQUEIDENTIFIER = (SELECT role_id FROM roles WHERE role_name = 'nurse');
DECLARE @role_lab    UNIQUEIDENTIFIER = (SELECT role_id FROM roles WHERE role_name = 'lab_technician');
DECLARE @role_rec    UNIQUEIDENTIFIER = (SELECT role_id FROM roles WHERE role_name = 'receptionist');

IF NOT EXISTS (SELECT 1 FROM users WHERE username = 'Admin')
    INSERT INTO users (username, password_hash, email, role_id, first_name, last_name)
    VALUES ('Admin',
            '$2b$12$L0O0rO8vrmLeQnCycMw21eaqyxHzp6vDfIiBEzLgV8FzvXYuM7Npu',
            'admin@pdms.local', @role_admin, 'Admin', 'User');

IF NOT EXISTS (SELECT 1 FROM users WHERE username = 'AungZawMyo')
    INSERT INTO users (username, password_hash, email, role_id, first_name, last_name)
    VALUES ('AungZawMyo',
            '$2b$12$bgSiJnbttEozB.XRT.pAIOD0NRLAgnbak4OH7B5J5svsXgQ1kRQAC',
            'Dr.AungZawMyo@pdms.local', @role_doctor, 'Aung Zaw', 'Myo');

IF NOT EXISTS (SELECT 1 FROM users WHERE username = 'KayThiHtun')
    INSERT INTO users (username, password_hash, email, role_id, first_name, last_name)
    VALUES ('KayThiHtun',
            '$2b$12$Vy55lrt8JnDmmPKxS7WuDO0lkdBgsOsAaDsDXG6lHEizNNEK2flI.',
            'Dr.KayThiHtun@pdms.local', @role_doctor, 'Kay Thi', 'Htun');

IF NOT EXISTS (SELECT 1 FROM users WHERE username = 'SuLayNwe')
    INSERT INTO users (username, password_hash, email, role_id, first_name, last_name)
    VALUES ('SuLayNwe',
            '$2b$12$9G7r.nOe.XNwo81HpxKn0.71gaEN3XjzRdF6qgn1SLbGK0PvKTmaC',
            'RN.SuLayNwe@pdms.local', @role_nurse, 'Su Lay', 'Nwe');

IF NOT EXISTS (SELECT 1 FROM users WHERE username = 'PhyoWai')
    INSERT INTO users (username, password_hash, email, role_id, first_name, last_name)
    VALUES ('PhyoWai',
            '$2b$12$GkkUhhWzpJGwob.pUO6oLepjMVzpjQ11R0tbIpgPqmz2pmNytWZvO',
            'Lab.PhyoWai@pdms.local', @role_lab, 'Phyo', 'Wai');

IF NOT EXISTS (SELECT 1 FROM users WHERE username = 'MayThae')
    INSERT INTO users (username, password_hash, email, role_id, first_name, last_name)
    VALUES ('MayThae',
            '$2b$12$PMXZVEGVunvj42WhBiZEgO2f.ZbxyrMbkdWGoW/jrQzB5/dAORNFq',
            'Rec.MayThae@pdms.local', @role_rec, 'May', 'Thae');

PRINT 'Users done.';
GO


-- ============================================================
-- SECTION 2: PATIENTS
-- ============================================================
PRINT '--- Inserting patients ---';

-- Patient 1: Ko Min Thu (male, 35) — has Penicillin allergy
IF NOT EXISTS (SELECT 1 FROM patients WHERE mrn = 'PDMS-2026-00001')
    INSERT INTO patients (mrn, first_name, last_name, date_of_birth, gender, blood_type,
                          phone, email, address,
                          emergency_contact_name, emergency_contact_phone)
    VALUES ('PDMS-2026-00001', 'Min Thu', 'Ko', '1990-05-15', 'male', 'O+',
            '09-111-22333', 'minthu@gmail.com', 'No.12, Myoma Street, Yangon',
            'Aye Aye (wife)', '09-444-55666');

-- Patient 2: Ma Aye Aye (female, 27) — no allergies, no history
IF NOT EXISTS (SELECT 1 FROM patients WHERE mrn = 'PDMS-2026-00002')
    INSERT INTO patients (mrn, first_name, last_name, date_of_birth, gender, blood_type,
                          phone, email, address)
    VALUES ('PDMS-2026-00002', 'Aye Aye', 'Ma', '1998-11-22', 'female', 'A+',
            '09-222-33444', 'ayeaye@gmail.com', 'No.45, Pazundaung, Yangon');

-- Patient 3: U Kyaw Zin (male, 62) — Type 2 Diabetes + Hypertension (chronic)
IF NOT EXISTS (SELECT 1 FROM patients WHERE mrn = 'PDMS-2026-00003')
    INSERT INTO patients (mrn, first_name, last_name, date_of_birth, gender, blood_type,
                          phone, address,
                          emergency_contact_name, emergency_contact_phone)
    VALUES ('PDMS-2026-00003', 'Kyaw Zin', 'U', '1963-07-08', 'male', 'B+',
            '09-333-44555', 'No.88, Insein Road, Yangon',
            'Ma Khin Khin (daughter)', '09-777-88999');

-- Patient 4: Daw Hla Hla (female, 47) — Aspirin allergy
IF NOT EXISTS (SELECT 1 FROM patients WHERE mrn = 'PDMS-2026-00004')
    INSERT INTO patients (mrn, first_name, last_name, date_of_birth, gender, blood_type,
                          phone, address)
    VALUES ('PDMS-2026-00004', 'Hla Hla', 'Daw', '1979-03-30', 'female', 'AB+',
            '09-444-55777', 'No.23, Tamwe Township, Yangon');

PRINT 'Patients done.';
GO


-- ============================================================
-- SECTION 3: ALLERGIES
-- ============================================================
PRINT '--- Inserting allergies ---';

DECLARE @dr_azm_id UNIQUEIDENTIFIER = (SELECT user_id FROM users WHERE username = 'AungZawMyo');

-- Ko Min Thu: Penicillin — SEVERE (blocks usp_record_prescription for Penicillin)
IF NOT EXISTS (
    SELECT 1 FROM allergies
    WHERE patient_id = (SELECT patient_id FROM patients WHERE mrn = 'PDMS-2026-00001')
      AND allergen = 'Penicillin'
)
    INSERT INTO allergies (patient_id, allergen, reaction_type, severity, recorded_by, event_date)
    VALUES (
        (SELECT patient_id FROM patients WHERE mrn = 'PDMS-2026-00001'),
        'Penicillin', 'Rash and anaphylaxis', 'severe', @dr_azm_id, '2020-03-10'
    );

-- Daw Hla Hla: Aspirin — MILD
IF NOT EXISTS (
    SELECT 1 FROM allergies
    WHERE patient_id = (SELECT patient_id FROM patients WHERE mrn = 'PDMS-2026-00004')
      AND allergen = 'Aspirin'
)
    INSERT INTO allergies (patient_id, allergen, reaction_type, severity, recorded_by, event_date)
    VALUES (
        (SELECT patient_id FROM patients WHERE mrn = 'PDMS-2026-00004'),
        'Aspirin', 'Gastric irritation and nausea', 'mild', @dr_azm_id, '2019-06-01'
    );

PRINT 'Allergies done.';
GO


-- ============================================================
-- SECTION 4: MEDICAL HISTORY
-- ============================================================
PRINT '--- Inserting medical history ---';

DECLARE @dr_azm_id UNIQUEIDENTIFIER = (SELECT user_id FROM users WHERE username = 'AungZawMyo');

-- U Kyaw Zin: Type 2 Diabetes Mellitus (chronic)
IF NOT EXISTS (
    SELECT 1 FROM medical_history
    WHERE patient_id = (SELECT patient_id FROM patients WHERE mrn = 'PDMS-2026-00003')
      AND condition_name = 'Type 2 Diabetes Mellitus'
)
    INSERT INTO medical_history (patient_id, condition_name, icd_code, onset_date, is_chronic, recorded_by, event_date)
    VALUES (
        (SELECT patient_id FROM patients WHERE mrn = 'PDMS-2026-00003'),
        'Type 2 Diabetes Mellitus', 'E11', '2015-04-20', 1, @dr_azm_id, '2015-04-20'
    );

-- U Kyaw Zin: Essential Hypertension (chronic)
IF NOT EXISTS (
    SELECT 1 FROM medical_history
    WHERE patient_id = (SELECT patient_id FROM patients WHERE mrn = 'PDMS-2026-00003')
      AND condition_name = 'Essential Hypertension'
)
    INSERT INTO medical_history (patient_id, condition_name, icd_code, onset_date, is_chronic, recorded_by, event_date)
    VALUES (
        (SELECT patient_id FROM patients WHERE mrn = 'PDMS-2026-00003'),
        'Essential Hypertension', 'I10', '2018-09-11', 1, @dr_azm_id, '2018-09-11'
    );

-- Ko Min Thu: Seasonal allergic rhinitis (resolved)
IF NOT EXISTS (
    SELECT 1 FROM medical_history
    WHERE patient_id = (SELECT patient_id FROM patients WHERE mrn = 'PDMS-2026-00001')
      AND condition_name = 'Seasonal Allergic Rhinitis'
)
    INSERT INTO medical_history (patient_id, condition_name, icd_code, onset_date, resolution_date, is_chronic, recorded_by, event_date)
    VALUES (
        (SELECT patient_id FROM patients WHERE mrn = 'PDMS-2026-00001'),
        'Seasonal Allergic Rhinitis', 'J30.1', '2018-01-01', '2022-12-31', 0, @dr_azm_id, '2018-01-01'
    );

PRINT 'Medical history done.';
GO


-- ============================================================
-- SECTION 5: APPOINTMENTS
-- ============================================================
PRINT '--- Inserting appointments ---';

DECLARE @dr_azm_id UNIQUEIDENTIFIER = (SELECT user_id FROM users WHERE username = 'AungZawMyo');
DECLARE @dr_kth_id UNIQUEIDENTIFIER = (SELECT user_id FROM users WHERE username = 'KayThiHtun');
DECLARE @rec_id    UNIQUEIDENTIFIER = (SELECT user_id FROM users WHERE username = 'MayThae');
DECLARE @pt1_id    UNIQUEIDENTIFIER = (SELECT patient_id FROM patients WHERE mrn = 'PDMS-2026-00001');
DECLARE @pt2_id    UNIQUEIDENTIFIER = (SELECT patient_id FROM patients WHERE mrn = 'PDMS-2026-00002');
DECLARE @pt3_id    UNIQUEIDENTIFIER = (SELECT patient_id FROM patients WHERE mrn = 'PDMS-2026-00003');
DECLARE @pt4_id    UNIQUEIDENTIFIER = (SELECT patient_id FROM patients WHERE mrn = 'PDMS-2026-00004');

-- Appointment 1: Ko Min Thu + Dr. AZM — COMPLETED (linked to encounter below)
IF NOT EXISTS (SELECT 1 FROM appointments WHERE patient_id = @pt1_id AND scheduled_at = '2026-04-10 09:00')
    INSERT INTO appointments (patient_id, doctor_id, scheduled_at, reason, status, created_by)
    VALUES (@pt1_id, @dr_azm_id, '2026-04-10 09:00',
            'Sore throat and fever for 3 days', 'completed', @rec_id);

-- Appointment 2: Ma Aye Aye + Dr. Kay Thi Htun — SCHEDULED
IF NOT EXISTS (SELECT 1 FROM appointments WHERE patient_id = @pt2_id AND scheduled_at = '2026-04-11 10:30')
    INSERT INTO appointments (patient_id, doctor_id, scheduled_at, reason, status, created_by)
    VALUES (@pt2_id, @dr_kth_id, '2026-04-11 10:30',
            'Routine annual check-up', 'scheduled', @rec_id);

-- Appointment 3: U Kyaw Zin + Dr. AZM — CONFIRMED
IF NOT EXISTS (SELECT 1 FROM appointments WHERE patient_id = @pt3_id AND scheduled_at = '2026-04-12 14:00')
    INSERT INTO appointments (patient_id, doctor_id, scheduled_at, reason, status, created_by)
    VALUES (@pt3_id, @dr_azm_id, '2026-04-12 14:00',
            'Diabetes and hypertension follow-up', 'confirmed', @rec_id);

-- Appointment 4: Daw Hla Hla + Dr. Kay Thi Htun — SCHEDULED
IF NOT EXISTS (SELECT 1 FROM appointments WHERE patient_id = @pt4_id AND scheduled_at = '2026-04-14 11:00')
    INSERT INTO appointments (patient_id, doctor_id, scheduled_at, reason, status, created_by)
    VALUES (@pt4_id, @dr_kth_id, '2026-04-14 11:00',
            'Knee pain and joint swelling', 'scheduled', @rec_id);

PRINT 'Appointments done.';
GO


-- ============================================================
-- SECTION 6: ENCOUNTER  (Ko Min Thu  —  via stored proc)
-- ============================================================
PRINT '--- Creating encounter for Ko Min Thu ---';

DECLARE @dr_azm_id    UNIQUEIDENTIFIER = (SELECT user_id FROM users WHERE username = 'AungZawMyo');
DECLARE @pt1_id       UNIQUEIDENTIFIER = (SELECT patient_id FROM patients WHERE mrn = 'PDMS-2026-00001');
DECLARE @appt1_id     UNIQUEIDENTIFIER = (
    SELECT TOP 1 appointment_id FROM appointments
    WHERE patient_id = @pt1_id
      AND scheduled_at = '2026-04-10 09:00'
);
DECLARE @encounter_id UNIQUEIDENTIFIER;

IF NOT EXISTS (SELECT 1 FROM encounters WHERE patient_id = @pt1_id)
BEGIN
    EXEC usp_create_encounter
        @p_patient_id      = @pt1_id,
        @p_doctor_id       = @dr_azm_id,
        @p_appointment_id  = @appt1_id,
        @p_encounter_type  = 'outpatient',
        @p_chief_complaint = 'Sore throat and fever for 3 days',
        @p_created_by      = @dr_azm_id,
        @p_encounter_id    = @encounter_id OUTPUT;
    PRINT 'Encounter created.';
END
ELSE
    SELECT @encounter_id = encounter_id FROM encounters WHERE patient_id = @pt1_id;

-- Fill in the SOAP note (shell was created by the stored proc)
UPDATE clinical_notes
SET subjective  = 'Patient reports sore throat, fever (38.5°C), and general malaise for 3 days. Denies cough or shortness of breath. No known sick contacts.',
    objective   = 'Temperature: 38.5°C, BP: 120/80 mmHg, HR: 88 bpm, SpO2: 98%, RR: 16. Throat is erythematous with mild tonsillar hypertrophy. No cervical lymphadenopathy.',
    assessment  = 'Acute pharyngitis (J02.9). Likely bacterial aetiology given duration and clinical presentation. Penicillin allergy documented — macrolide prescribed.',
    [plan]      = 'Azithromycin 500mg once daily x 3 days. Increase fluid intake. Rest for 2 days. Paracetamol 500mg PRN for fever. Review if no improvement in 48 hours.',
    updated_at  = GETDATE()
WHERE encounter_id = @encounter_id;

PRINT 'SOAP note updated.';
GO


-- ============================================================
-- SECTION 7: VITALS  (recorded by nurse Su Lay Nwe)
-- ============================================================
PRINT '--- Inserting vitals ---';

DECLARE @pt1_id       UNIQUEIDENTIFIER = (SELECT patient_id FROM patients WHERE mrn = 'PDMS-2026-00001');
DECLARE @nurse_id     UNIQUEIDENTIFIER = (SELECT user_id FROM users WHERE username = 'SuLayNwe');
DECLARE @encounter_id UNIQUEIDENTIFIER = (
    SELECT TOP 1 encounter_id FROM encounters WHERE patient_id = @pt1_id
);

IF NOT EXISTS (SELECT 1 FROM vitals WHERE encounter_id = @encounter_id)
    INSERT INTO vitals (
        patient_id, encounter_id, recorded_by,
        blood_pressure_sys, blood_pressure_dia,
        heart_rate, temperature,
        weight_kg, height_cm,
        oxygen_saturation, respiratory_rate
    )
    VALUES (
        @pt1_id, @encounter_id, @nurse_id,
        120, 80,
        88, 38.5,
        68.0, 172.0,
        98, 16
    );

PRINT 'Vitals done.';
GO


-- ============================================================
-- SECTION 8: DIAGNOSIS
-- ============================================================
PRINT '--- Inserting diagnosis ---';

DECLARE @pt1_id       UNIQUEIDENTIFIER = (SELECT patient_id FROM patients WHERE mrn = 'PDMS-2026-00001');
DECLARE @dr_azm_id    UNIQUEIDENTIFIER = (SELECT user_id FROM users WHERE username = 'AungZawMyo');
DECLARE @encounter_id UNIQUEIDENTIFIER = (
    SELECT TOP 1 encounter_id FROM encounters WHERE patient_id = @pt1_id
);

IF NOT EXISTS (SELECT 1 FROM diagnoses WHERE encounter_id = @encounter_id)
    INSERT INTO diagnoses (
        encounter_id, patient_id,
        icd_code, description,
        diagnosis_type, condition, timing,
        is_chronic, diagnosed_by, event_date
    )
    VALUES (
        @encounter_id, @pt1_id,
        'J02.9', 'Acute pharyngitis, unspecified',
        'primary', 'confirmed', 'acute',
        0, @dr_azm_id, '2026-04-10'
    );

PRINT 'Diagnosis done.';
GO


-- ============================================================
-- SECTION 9: PRESCRIPTION  (via stored proc — allergy-safe drug)
-- NOTE: Ko Min Thu is allergic to Penicillin.
--       Azithromycin (macrolide) is prescribed — safe for this patient.
--       Attempting to prescribe 'Penicillin' here would raise ALLERGY_CONFLICT.
-- ============================================================
PRINT '--- Inserting prescription ---';

DECLARE @pt1_id       UNIQUEIDENTIFIER = (SELECT patient_id FROM patients WHERE mrn = 'PDMS-2026-00001');
DECLARE @dr_azm_id    UNIQUEIDENTIFIER = (SELECT user_id FROM users WHERE username = 'AungZawMyo');
DECLARE @encounter_id UNIQUEIDENTIFIER = (
    SELECT TOP 1 encounter_id FROM encounters WHERE patient_id = @pt1_id
);
DECLARE @rx_id UNIQUEIDENTIFIER;

IF NOT EXISTS (SELECT 1 FROM prescriptions WHERE encounter_id = @encounter_id)
BEGIN
    EXEC usp_record_prescription
        @p_encounter_id    = @encounter_id,
        @p_patient_id      = @pt1_id,
        @p_doctor_id       = @dr_azm_id,
        @p_drug_name       = 'Azithromycin',
        @p_dosage          = '500mg',
        @p_frequency       = 'Once daily',
        @p_duration        = '3 days',
        @p_route           = 'oral',
        @p_instructions    = 'Take with food. Complete the full 3-day course even if symptoms improve.',
        @p_prescription_id = @rx_id OUTPUT;
    PRINT 'Prescription created.';
END

-- Also add Paracetamol for fever (PRN)
EXEC usp_record_prescription
    @p_encounter_id    = @encounter_id,
    @p_patient_id      = @pt1_id,
    @p_doctor_id       = @dr_azm_id,
    @p_drug_name       = 'Paracetamol',
    @p_dosage          = '500mg',
    @p_frequency       = 'Every 6 hours as needed',
    @p_duration        = '3 days',
    @p_route           = 'oral',
    @p_instructions    = 'Take only when temperature exceeds 38°C. Do not exceed 4 doses per day.',
    @p_prescription_id = @rx_id OUTPUT;

PRINT 'Prescriptions done.';
GO


-- ============================================================
-- SECTION 10: LAB ORDER  (CBC ordered by Dr. AZM)
-- ============================================================
PRINT '--- Inserting lab order ---';

DECLARE @pt1_id       UNIQUEIDENTIFIER = (SELECT patient_id FROM patients WHERE mrn = 'PDMS-2026-00001');
DECLARE @dr_azm_id    UNIQUEIDENTIFIER = (SELECT user_id FROM users WHERE username = 'AungZawMyo');
DECLARE @encounter_id UNIQUEIDENTIFIER = (
    SELECT TOP 1 encounter_id FROM encounters WHERE patient_id = @pt1_id
);
DECLARE @cbc_tmpl_id  UNIQUEIDENTIFIER = (SELECT template_id FROM lab_test_templates WHERE test_code = 'CBC');
DECLARE @order_id     UNIQUEIDENTIFIER = NEWID();

IF NOT EXISTS (SELECT 1 FROM lab_orders WHERE encounter_id = @encounter_id AND test_code = 'CBC')
    INSERT INTO lab_orders (
        order_id, encounter_id, patient_id, ordered_by,
        template_id, test_name, test_code, test_category,
        priority, status
    )
    VALUES (
        @order_id, @encounter_id, @pt1_id, @dr_azm_id,
        @cbc_tmpl_id, 'Complete Blood Count', 'CBC', 'hematology',
        'routine', 'ordered'
    );
ELSE
    SELECT @order_id = order_id FROM lab_orders WHERE encounter_id = @encounter_id AND test_code = 'CBC';

PRINT 'Lab order done.';
GO


-- ============================================================
-- SECTION 11: LAB RESULTS  (uploaded by Phyo Wai)
-- WBC elevated — suggests infection (consistent with pharyngitis diagnosis)
-- ============================================================
PRINT '--- Inserting lab results ---';

DECLARE @pt1_id     UNIQUEIDENTIFIER = (SELECT patient_id FROM patients WHERE mrn = 'PDMS-2026-00001');
DECLARE @lab_user   UNIQUEIDENTIFIER = (SELECT user_id FROM users WHERE username = 'PhyoWai');
DECLARE @order_id   UNIQUEIDENTIFIER = (
    SELECT TOP 1 order_id FROM lab_orders
    WHERE patient_id = @pt1_id AND test_code = 'CBC'
);
DECLARE @cbc_tmpl   UNIQUEIDENTIFIER = (SELECT template_id FROM lab_test_templates WHERE test_code = 'CBC');

IF NOT EXISTS (SELECT 1 FROM lab_results WHERE order_id = @order_id)
BEGIN
    -- WBC: 11.2 (HIGH — normal 4.0–10.0, supports bacterial infection)
    INSERT INTO lab_results (order_id, patient_id, parameter_id, uploaded_by, parameter_name, result_value, unit, normal_range, is_abnormal, abnormal_level)
    SELECT @order_id, @pt1_id, parameter_id, @lab_user,
           'WBC', '11.2', '10^9/L', '4.0 – 10.0', 1, 'high'
    FROM lab_test_parameters WHERE template_id = @cbc_tmpl AND parameter_name = 'WBC';

    -- RBC: 4.8 (normal)
    INSERT INTO lab_results (order_id, patient_id, parameter_id, uploaded_by, parameter_name, result_value, unit, normal_range, is_abnormal)
    SELECT @order_id, @pt1_id, parameter_id, @lab_user,
           'RBC', '4.8', '10^12/L', '4.5 – 5.5', 0
    FROM lab_test_parameters WHERE template_id = @cbc_tmpl AND parameter_name = 'RBC';

    -- Hemoglobin: 14.2 (normal)
    INSERT INTO lab_results (order_id, patient_id, parameter_id, uploaded_by, parameter_name, result_value, unit, normal_range, is_abnormal)
    SELECT @order_id, @pt1_id, parameter_id, @lab_user,
           'Hemoglobin', '14.2', 'g/dL', '13.5 – 17.5', 0
    FROM lab_test_parameters WHERE template_id = @cbc_tmpl AND parameter_name = 'Hemoglobin';

    -- Hematocrit: 42.5 (normal)
    INSERT INTO lab_results (order_id, patient_id, parameter_id, uploaded_by, parameter_name, result_value, unit, normal_range, is_abnormal)
    SELECT @order_id, @pt1_id, parameter_id, @lab_user,
           'Hematocrit', '42.5', '%', '41 – 53', 0
    FROM lab_test_parameters WHERE template_id = @cbc_tmpl AND parameter_name = 'Hematocrit';

    -- Platelets: 285 (normal)
    INSERT INTO lab_results (order_id, patient_id, parameter_id, uploaded_by, parameter_name, result_value, unit, normal_range, is_abnormal)
    SELECT @order_id, @pt1_id, parameter_id, @lab_user,
           'Platelets', '285', '10^9/L', '150 – 400', 0
    FROM lab_test_parameters WHERE template_id = @cbc_tmpl AND parameter_name = 'Platelets';

    -- Mark order as completed
    UPDATE lab_orders SET status = 'completed' WHERE order_id = @order_id;

    PRINT 'Lab results done.';
END
GO


-- ============================================================
-- SUMMARY
-- ============================================================
PRINT '';
PRINT '=== Test data loaded successfully ===';
PRINT '';
SELECT 'Users'        AS [Table], COUNT(*) AS [Rows] FROM users
UNION ALL
SELECT 'Patients',      COUNT(*) FROM patients
UNION ALL
SELECT 'Allergies',     COUNT(*) FROM allergies
UNION ALL
SELECT 'MedHistory',    COUNT(*) FROM medical_history
UNION ALL
SELECT 'Appointments',  COUNT(*) FROM appointments
UNION ALL
SELECT 'Encounters',    COUNT(*) FROM encounters
UNION ALL
SELECT 'ClinicalNotes', COUNT(*) FROM clinical_notes
UNION ALL
SELECT 'Vitals',        COUNT(*) FROM vitals
UNION ALL
SELECT 'Diagnoses',     COUNT(*) FROM diagnoses
UNION ALL
SELECT 'Prescriptions', COUNT(*) FROM prescriptions
UNION ALL
SELECT 'LabOrders',     COUNT(*) FROM lab_orders
UNION ALL
SELECT 'LabResults',    COUNT(*) FROM lab_results;
GO
