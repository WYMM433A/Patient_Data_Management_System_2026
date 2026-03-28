USE pdms_db;
GO

-- ============================================================
-- MODULE: MEDICATIONS
-- Tables: prescriptions
-- Run order: 05 — depends on 01 (users), 02 (patients), 04 (encounters)
-- Note: Allergy safety check is enforced by usp_record_prescription
--       stored procedure (defined in 11_stored_procs.sql).
-- ============================================================

-- 14. PRESCRIPTIONS
IF OBJECT_ID('dbo.prescriptions', 'U') IS NULL
BEGIN
    CREATE TABLE prescriptions (
        prescription_id UNIQUEIDENTIFIER  NOT NULL CONSTRAINT PK_prescriptions PRIMARY KEY DEFAULT NEWID(),
        encounter_id    UNIQUEIDENTIFIER  NOT NULL,
        patient_id      UNIQUEIDENTIFIER  NOT NULL,
        doctor_id       UNIQUEIDENTIFIER  NOT NULL,
        drug_name       NVARCHAR(200)     NOT NULL,
        dosage          NVARCHAR(50),
        frequency       NVARCHAR(50),
        duration        NVARCHAR(50),
        route           NVARCHAR(30)
                            CONSTRAINT CHK_rx_route
                                CHECK (route IN ('oral', 'IV', 'topical', 'inhaled', 'subcutaneous')),
        instructions    NVARCHAR(MAX),
        is_active       BIT               NOT NULL DEFAULT 1,
        is_removed      BIT               NOT NULL DEFAULT 0,  -- soft delete
        issued_at       DATETIME2         NOT NULL DEFAULT GETDATE(),
        event_date      DATETIME2,
        validated_at    DATETIME2,
        CONSTRAINT FK_rx_encounter FOREIGN KEY (encounter_id) REFERENCES encounters(encounter_id),
        CONSTRAINT FK_rx_patient   FOREIGN KEY (patient_id)   REFERENCES patients(patient_id),
        CONSTRAINT FK_rx_doctor    FOREIGN KEY (doctor_id)    REFERENCES users(user_id)
    );
    PRINT 'Table prescriptions created.';
END
ELSE
    PRINT 'Table prescriptions already exists — skipped.';
GO
