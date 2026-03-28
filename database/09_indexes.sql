USE pdms_db;
GO

-- ============================================================
-- PERFORMANCE INDEXES + FULL-TEXT SEARCH
-- Run order: 09 — run after all tables (01–08) are created
-- ============================================================

-- patients
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_patients_mrn' AND object_id = OBJECT_ID('patients'))
    CREATE INDEX idx_patients_mrn  ON patients(mrn);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_patients_name' AND object_id = OBJECT_ID('patients'))
    CREATE INDEX idx_patients_name ON patients(last_name, first_name);
GO

-- encounters
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_encounters_patient' AND object_id = OBJECT_ID('encounters'))
    CREATE INDEX idx_encounters_patient ON encounters(patient_id);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_encounters_doctor' AND object_id = OBJECT_ID('encounters'))
    CREATE INDEX idx_encounters_doctor  ON encounters(doctor_id);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_encounters_date' AND object_id = OBJECT_ID('encounters'))
    CREATE INDEX idx_encounters_date    ON encounters(encounter_date);
GO

-- lab_orders
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_lab_orders_patient' AND object_id = OBJECT_ID('lab_orders'))
    CREATE INDEX idx_lab_orders_patient ON lab_orders(patient_id);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_lab_orders_status' AND object_id = OBJECT_ID('lab_orders'))
    CREATE INDEX idx_lab_orders_status  ON lab_orders(status);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_lab_orders_ordered_at' AND object_id = OBJECT_ID('lab_orders'))
    CREATE INDEX idx_lab_orders_ordered_at ON lab_orders(ordered_at);
GO

-- lab_results
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_lab_results_abnormal' AND object_id = OBJECT_ID('lab_results'))
    CREATE INDEX idx_lab_results_abnormal ON lab_results(is_abnormal);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_lab_results_order' AND object_id = OBJECT_ID('lab_results'))
    CREATE INDEX idx_lab_results_order    ON lab_results(order_id);
GO

-- diagnoses
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_diagnoses_icd' AND object_id = OBJECT_ID('diagnoses'))
    CREATE INDEX idx_diagnoses_icd     ON diagnoses(icd_code);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_diagnoses_patient' AND object_id = OBJECT_ID('diagnoses'))
    CREATE INDEX idx_diagnoses_patient ON diagnoses(patient_id);
GO

-- vitals
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_vitals_patient' AND object_id = OBJECT_ID('vitals'))
    CREATE INDEX idx_vitals_patient ON vitals(patient_id);
GO

-- prescriptions
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_prescriptions_patient' AND object_id = OBJECT_ID('prescriptions'))
    CREATE INDEX idx_prescriptions_patient ON prescriptions(patient_id);
GO

-- audit_logs
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_audit_logs_user' AND object_id = OBJECT_ID('audit_logs'))
    CREATE INDEX idx_audit_logs_user      ON audit_logs(user_id);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_audit_logs_timestamp' AND object_id = OBJECT_ID('audit_logs'))
    CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp);
GO

-- appointments
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_appointments_patient' AND object_id = OBJECT_ID('appointments'))
    CREATE INDEX idx_appointments_patient ON appointments(patient_id);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_appointments_doctor' AND object_id = OBJECT_ID('appointments'))
    CREATE INDEX idx_appointments_doctor  ON appointments(doctor_id);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_appointments_scheduled' AND object_id = OBJECT_ID('appointments'))
    CREATE INDEX idx_appointments_scheduled ON appointments(scheduled_at);
GO

PRINT 'All indexes created.';
GO

-- ============================================================
-- FULL-TEXT SEARCH SETUP
-- Requires Full-Text Search feature installed with SQL Server.
-- Verify: SELECT FULLTEXTSERVICEPROPERTY('IsFullTextInstalled')
-- Should return 1. If 0, install via SQL Server Setup > Features.
-- ============================================================

IF FULLTEXTSERVICEPROPERTY('IsFullTextInstalled') = 1
BEGIN
    -- Create FTS catalog if not exists
    IF NOT EXISTS (SELECT * FROM sys.fulltext_catalogs WHERE name = 'pdms_fts_catalog')
    BEGIN
        CREATE FULLTEXT CATALOG pdms_fts_catalog AS DEFAULT;
        PRINT 'Full-text catalog pdms_fts_catalog created.';
    END

    -- FTS index on clinical_notes (SOAP fields)
    IF NOT EXISTS (
        SELECT * FROM sys.fulltext_indexes
        WHERE object_id = OBJECT_ID('dbo.clinical_notes')
    )
    BEGIN
        CREATE FULLTEXT INDEX ON clinical_notes(
            subjective, objective, assessment, [plan]
        )
        KEY INDEX PK_clinical_notes
        ON pdms_fts_catalog;
        PRINT 'FTS index on clinical_notes created.';
    END

    -- FTS index on diagnoses (description field)
    IF NOT EXISTS (
        SELECT * FROM sys.fulltext_indexes
        WHERE object_id = OBJECT_ID('dbo.diagnoses')
    )
    BEGIN
        CREATE FULLTEXT INDEX ON diagnoses(description)
        KEY INDEX PK_diagnoses
        ON pdms_fts_catalog;
        PRINT 'FTS index on diagnoses created.';
    END
END
ELSE
    PRINT 'WARNING: Full-Text Search is not installed. FTS indexes skipped.';
GO

-- Usage example (once FTS is set up):
-- SELECT * FROM clinical_notes
-- WHERE CONTAINS((subjective, objective, assessment, [plan]), 'chest pain');
--
-- SELECT * FROM diagnoses
-- WHERE CONTAINS(description, 'hypertension');
