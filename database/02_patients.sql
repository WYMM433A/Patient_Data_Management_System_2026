USE pdms_db;
GO

-- ============================================================
-- MODULE: PATIENTS
-- Tables: patients, medical_history, allergies, vaccinations
-- Run order: 02 — depends on 01 (users)
-- ============================================================

-- 5. PATIENTS
IF OBJECT_ID('dbo.patients', 'U') IS NULL
BEGIN
    CREATE TABLE patients (
        patient_id              UNIQUEIDENTIFIER  NOT NULL CONSTRAINT PK_patients PRIMARY KEY DEFAULT NEWID(),
        mrn                     NVARCHAR(20)      NOT NULL CONSTRAINT UQ_patients_mrn UNIQUE,
        first_name              NVARCHAR(100)     NOT NULL,
        last_name               NVARCHAR(100)     NOT NULL,
        date_of_birth           DATE              NOT NULL,
        gender                  NVARCHAR(20),
        blood_type              NVARCHAR(5),
        phone                   NVARCHAR(20),
        email                   NVARCHAR(150),
        address                 NVARCHAR(MAX),
        emergency_contact_name  NVARCHAR(150),
        emergency_contact_phone NVARCHAR(20),
        created_at              DATETIME2         NOT NULL DEFAULT GETDATE()
        -- MRN format: PDMS-YYYY-NNNNN (e.g. PDMS-2026-00142)
        -- MRN is generated in the Python service layer, not the DB.
    );
    PRINT 'Table patients created.';
END
ELSE
    PRINT 'Table patients already exists — skipped.';
GO

-- 6. MEDICAL_HISTORY
IF OBJECT_ID('dbo.medical_history', 'U') IS NULL
BEGIN
    CREATE TABLE medical_history (
        history_id      UNIQUEIDENTIFIER  NOT NULL CONSTRAINT PK_medical_history PRIMARY KEY DEFAULT NEWID(),
        patient_id      UNIQUEIDENTIFIER  NOT NULL,
        condition_name  NVARCHAR(200)     NOT NULL,
        icd_code        NVARCHAR(10),
        onset_date      DATE,
        resolution_date DATE,                       -- NULL = condition still ongoing
        is_chronic      BIT               NOT NULL DEFAULT 0,
        is_removed      BIT               NOT NULL DEFAULT 0,  -- soft delete
        valid_from      DATE,
        valid_until     DATE,
        notes           NVARCHAR(MAX),
        recorded_by     UNIQUEIDENTIFIER,
        recorded_at     DATETIME2         NOT NULL DEFAULT GETDATE(),
        event_date      DATE,
        validated_at    DATETIME2,
        CONSTRAINT FK_mh_patient     FOREIGN KEY (patient_id)  REFERENCES patients(patient_id),
        CONSTRAINT FK_mh_recorded_by FOREIGN KEY (recorded_by) REFERENCES users(user_id)
    );
    PRINT 'Table medical_history created.';
END
ELSE
    PRINT 'Table medical_history already exists — skipped.';
GO

-- 7. ALLERGIES
IF OBJECT_ID('dbo.allergies', 'U') IS NULL
BEGIN
    CREATE TABLE allergies (
        allergy_id    UNIQUEIDENTIFIER  NOT NULL CONSTRAINT PK_allergies PRIMARY KEY DEFAULT NEWID(),
        patient_id    UNIQUEIDENTIFIER  NOT NULL,
        allergen      NVARCHAR(200)     NOT NULL,
        reaction_type NVARCHAR(100),
        severity      NVARCHAR(20)      CONSTRAINT CHK_allergy_severity
                                            CHECK (severity IN ('mild', 'moderate', 'severe')),
        is_removed    BIT               NOT NULL DEFAULT 0,  -- soft delete
        valid_from    DATE,
        valid_until   DATE,
        recorded_by   UNIQUEIDENTIFIER,
        recorded_at   DATETIME2         NOT NULL DEFAULT GETDATE(),
        event_date    DATE,
        validated_at  DATETIME2,
        CONSTRAINT FK_allergy_patient      FOREIGN KEY (patient_id)  REFERENCES patients(patient_id),
        CONSTRAINT FK_allergy_recorded_by  FOREIGN KEY (recorded_by) REFERENCES users(user_id)
    );
    PRINT 'Table allergies created.';
END
ELSE
    PRINT 'Table allergies already exists — skipped.';
GO

-- 8. VACCINATIONS
IF OBJECT_ID('dbo.vaccinations', 'U') IS NULL
BEGIN
    CREATE TABLE vaccinations (
        vaccination_id  UNIQUEIDENTIFIER  NOT NULL CONSTRAINT PK_vaccinations PRIMARY KEY DEFAULT NEWID(),
        patient_id      UNIQUEIDENTIFIER  NOT NULL,
        vaccine_name    NVARCHAR(200)     NOT NULL,
        dose_number     INT,
        administered_by UNIQUEIDENTIFIER,
        administered_at DATE              NOT NULL,
        next_due_date   DATE,
        notes           NVARCHAR(MAX),
        recorded_at     DATETIME2         NOT NULL DEFAULT GETDATE(),
        event_date      DATE,
        validated_at    DATETIME2,
        CONSTRAINT FK_vacc_patient FOREIGN KEY (patient_id)      REFERENCES patients(patient_id),
        CONSTRAINT FK_vacc_admin   FOREIGN KEY (administered_by) REFERENCES users(user_id)
    );
    PRINT 'Table vaccinations created.';
END
ELSE
    PRINT 'Table vaccinations already exists — skipped.';
GO
