USE pdms_db;
GO

-- ============================================================
-- MODULE: CLINICAL ENCOUNTERS
-- Tables: encounters, clinical_notes, diagnoses, vitals
-- Run order: 04 — depends on 01 (users), 02 (patients), 03 (appointments)
-- ============================================================

-- 10. ENCOUNTERS
IF OBJECT_ID('dbo.encounters', 'U') IS NULL
BEGIN
    CREATE TABLE encounters (
        encounter_id    UNIQUEIDENTIFIER  NOT NULL CONSTRAINT PK_encounters PRIMARY KEY DEFAULT NEWID(),
        patient_id      UNIQUEIDENTIFIER  NOT NULL,
        doctor_id       UNIQUEIDENTIFIER  NOT NULL,
        appointment_id  UNIQUEIDENTIFIER,           -- NULL for walk-in
        encounter_date  DATETIME2         NOT NULL DEFAULT GETDATE(),
        encounter_type  NVARCHAR(20)      NOT NULL
                            CONSTRAINT CHK_enc_type
                                CHECK (encounter_type IN ('outpatient', 'follow-up', 'emergency')),
        chief_complaint NVARCHAR(MAX),
        status          NVARCHAR(10)      NOT NULL DEFAULT 'open'
                            CONSTRAINT CHK_enc_status
                                CHECK (status IN ('open', 'closed')),
        visit_number    INT               NOT NULL DEFAULT 1,
        created_at      DATETIME2         NOT NULL DEFAULT GETDATE(),
        closed_at       DATETIME2,
        CONSTRAINT FK_enc_patient     FOREIGN KEY (patient_id)     REFERENCES patients(patient_id),
        CONSTRAINT FK_enc_doctor      FOREIGN KEY (doctor_id)      REFERENCES users(user_id),
        CONSTRAINT FK_enc_appointment FOREIGN KEY (appointment_id) REFERENCES appointments(appointment_id)
    );
    PRINT 'Table encounters created.';
END
ELSE
    PRINT 'Table encounters already exists — skipped.';
GO

-- 11. CLINICAL_NOTES (SOAP format)
IF OBJECT_ID('dbo.clinical_notes', 'U') IS NULL
BEGIN
    CREATE TABLE clinical_notes (
        note_id      UNIQUEIDENTIFIER  NOT NULL CONSTRAINT PK_clinical_notes PRIMARY KEY DEFAULT NEWID(),
        encounter_id UNIQUEIDENTIFIER  NOT NULL,
        doctor_id    UNIQUEIDENTIFIER  NOT NULL,
        subjective   NVARCHAR(MAX),   -- S: patient's symptoms in their own words
        objective    NVARCHAR(MAX),   -- O: measurable findings (vitals, exams)
        assessment   NVARCHAR(MAX),   -- A: diagnosis / clinical impression
        [plan]       NVARCHAR(MAX),   -- P: treatment plan
        recorded_at  DATETIME2        NOT NULL DEFAULT GETDATE(),
        event_date   DATETIME2,
        validated_at DATETIME2,
        updated_at   DATETIME2,
        CONSTRAINT FK_notes_encounter FOREIGN KEY (encounter_id) REFERENCES encounters(encounter_id),
        CONSTRAINT FK_notes_doctor    FOREIGN KEY (doctor_id)    REFERENCES users(user_id)
    );
    PRINT 'Table clinical_notes created.';
END
ELSE
    PRINT 'Table clinical_notes already exists — skipped.';
GO

-- 12. DIAGNOSES
IF OBJECT_ID('dbo.diagnoses', 'U') IS NULL
BEGIN
    CREATE TABLE diagnoses (
        diagnosis_id   UNIQUEIDENTIFIER  NOT NULL CONSTRAINT PK_diagnoses PRIMARY KEY DEFAULT NEWID(),
        encounter_id   UNIQUEIDENTIFIER  NOT NULL,
        patient_id     UNIQUEIDENTIFIER  NOT NULL,
        icd_code       NVARCHAR(10)      NOT NULL,
        description    NVARCHAR(MAX),
        diagnosis_type NVARCHAR(20)      NOT NULL
                           CONSTRAINT CHK_diag_type
                               CHECK (diagnosis_type IN ('primary', 'secondary')),
        condition      NVARCHAR(20)
                           CONSTRAINT CHK_diag_condition
                               CHECK (condition IN ('suspected', 'confirmed', 'excluded', 'recurrent')),
        timing         NVARCHAR(20)
                           CONSTRAINT CHK_diag_timing
                               CHECK (timing IN ('acute', 'chronic', 'complication', 'recurrence')),
        is_chronic     BIT               NOT NULL DEFAULT 0,
        diagnosed_by   UNIQUEIDENTIFIER  NOT NULL,
        recorded_at    DATETIME2         NOT NULL DEFAULT GETDATE(),
        event_date     DATE,
        validated_at   DATETIME2,
        CONSTRAINT FK_diag_encounter   FOREIGN KEY (encounter_id)  REFERENCES encounters(encounter_id),
        CONSTRAINT FK_diag_patient     FOREIGN KEY (patient_id)    REFERENCES patients(patient_id),
        CONSTRAINT FK_diag_diagnosed_by FOREIGN KEY (diagnosed_by) REFERENCES users(user_id)
    );
    PRINT 'Table diagnoses created.';
END
ELSE
    PRINT 'Table diagnoses already exists — skipped.';
GO

-- 13. VITALS
-- Note: bmi is auto-calculated by trigger trg_calculate_bmi (defined in 10_triggers.sql)
-- Note: is_abnormal is auto-set by trigger trg_flag_abnormal_vitals (defined in 10_triggers.sql)
IF OBJECT_ID('dbo.vitals', 'U') IS NULL
BEGIN
    CREATE TABLE vitals (
        vital_id           UNIQUEIDENTIFIER  NOT NULL CONSTRAINT PK_vitals PRIMARY KEY DEFAULT NEWID(),
        patient_id         UNIQUEIDENTIFIER  NOT NULL,
        encounter_id       UNIQUEIDENTIFIER  NOT NULL,
        recorded_by        UNIQUEIDENTIFIER  NOT NULL,
        blood_pressure_sys INT,
        blood_pressure_dia INT,
        heart_rate         INT,
        temperature        DECIMAL(4,1),
        weight_kg          DECIMAL(5,2),
        height_cm          DECIMAL(5,2),
        oxygen_saturation  INT,
        respiratory_rate   INT,
        bmi                DECIMAL(4,2),    -- auto-calculated by trigger
        is_abnormal        BIT               NOT NULL DEFAULT 0,  -- auto-set by trigger
        recorded_at        DATETIME2         NOT NULL DEFAULT GETDATE(),
        event_date         DATETIME2,
        validated_at       DATETIME2,
        CONSTRAINT FK_vitals_patient   FOREIGN KEY (patient_id)   REFERENCES patients(patient_id),
        CONSTRAINT FK_vitals_encounter FOREIGN KEY (encounter_id) REFERENCES encounters(encounter_id),
        CONSTRAINT FK_vitals_recorded_by FOREIGN KEY (recorded_by) REFERENCES users(user_id)
    );
    PRINT 'Table vitals created.';
END
ELSE
    PRINT 'Table vitals already exists — skipped.';
GO
