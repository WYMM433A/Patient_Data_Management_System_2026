USE pdms_db;
GO

-- ============================================================
-- TRIGGERS
-- Run order: 10 — run after all tables (01–09) are created
--
-- Triggers defined here:
--  A) AUDIT TRIGGERS — one per clinical table (13 total)
--     Uses SESSION_CONTEXT to get user_id set by the FastAPI app.
--     App must call before each transaction:
--       EXEC sys.sp_set_session_context @key=N'user_id', @value=N'<uuid-string>'
--
--  B) trg_calculate_bmi     — auto-calculates BMI on vitals INSERT/UPDATE
--  C) trg_flag_abnormal_vitals — flags is_abnormal = 1 on vitals INSERT
-- ============================================================


-- ============================================================
-- A. AUDIT TRIGGERS (template repeated for each table)
-- ============================================================

-- encounters
DROP TRIGGER IF EXISTS dbo.trg_audit_encounters;
GO
CREATE TRIGGER trg_audit_encounters
ON encounters
AFTER INSERT, UPDATE, DELETE
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @action   NVARCHAR(10);
    DECLARE @user_id  UNIQUEIDENTIFIER = TRY_CAST(SESSION_CONTEXT(N'user_id') AS UNIQUEIDENTIFIER);
    DECLARE @record_id UNIQUEIDENTIFIER;

    IF EXISTS (SELECT 1 FROM inserted) AND EXISTS (SELECT 1 FROM deleted)
        SET @action = 'UPDATE';
    ELSE IF EXISTS (SELECT 1 FROM inserted)
        SET @action = 'CREATE';
    ELSE
        SET @action = 'DELETE';

    SELECT @record_id = encounter_id FROM inserted;
    IF @record_id IS NULL SELECT @record_id = encounter_id FROM deleted;

    INSERT INTO audit_logs (log_id, user_id, action, table_affected, record_id, old_value, new_value, timestamp)
    SELECT
        NEWID(), @user_id, @action, 'encounters', @record_id,
        (SELECT * FROM deleted  FOR JSON PATH),
        (SELECT * FROM inserted FOR JSON PATH),
        GETDATE();
END;
GO

-- clinical_notes
DROP TRIGGER IF EXISTS dbo.trg_audit_clinical_notes;
GO
CREATE TRIGGER trg_audit_clinical_notes
ON clinical_notes
AFTER INSERT, UPDATE, DELETE
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @action   NVARCHAR(10);
    DECLARE @user_id  UNIQUEIDENTIFIER = TRY_CAST(SESSION_CONTEXT(N'user_id') AS UNIQUEIDENTIFIER);
    DECLARE @record_id UNIQUEIDENTIFIER;

    IF EXISTS (SELECT 1 FROM inserted) AND EXISTS (SELECT 1 FROM deleted)
        SET @action = 'UPDATE';
    ELSE IF EXISTS (SELECT 1 FROM inserted)
        SET @action = 'CREATE';
    ELSE
        SET @action = 'DELETE';

    SELECT @record_id = note_id FROM inserted;
    IF @record_id IS NULL SELECT @record_id = note_id FROM deleted;

    INSERT INTO audit_logs (log_id, user_id, action, table_affected, record_id, old_value, new_value, timestamp)
    SELECT NEWID(), @user_id, @action, 'clinical_notes', @record_id,
        (SELECT * FROM deleted  FOR JSON PATH),
        (SELECT * FROM inserted FOR JSON PATH),
        GETDATE();
END;
GO

-- diagnoses
DROP TRIGGER IF EXISTS dbo.trg_audit_diagnoses;
GO
CREATE TRIGGER trg_audit_diagnoses
ON diagnoses
AFTER INSERT, UPDATE, DELETE
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @action   NVARCHAR(10);
    DECLARE @user_id  UNIQUEIDENTIFIER = TRY_CAST(SESSION_CONTEXT(N'user_id') AS UNIQUEIDENTIFIER);
    DECLARE @record_id UNIQUEIDENTIFIER;

    IF EXISTS (SELECT 1 FROM inserted) AND EXISTS (SELECT 1 FROM deleted)
        SET @action = 'UPDATE';
    ELSE IF EXISTS (SELECT 1 FROM inserted)
        SET @action = 'CREATE';
    ELSE
        SET @action = 'DELETE';

    SELECT @record_id = diagnosis_id FROM inserted;
    IF @record_id IS NULL SELECT @record_id = diagnosis_id FROM deleted;

    INSERT INTO audit_logs (log_id, user_id, action, table_affected, record_id, old_value, new_value, timestamp)
    SELECT NEWID(), @user_id, @action, 'diagnoses', @record_id,
        (SELECT * FROM deleted  FOR JSON PATH),
        (SELECT * FROM inserted FOR JSON PATH),
        GETDATE();
END;
GO

-- vitals
DROP TRIGGER IF EXISTS dbo.trg_audit_vitals;
GO
CREATE TRIGGER trg_audit_vitals
ON vitals
AFTER INSERT, UPDATE, DELETE
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @action   NVARCHAR(10);
    DECLARE @user_id  UNIQUEIDENTIFIER = TRY_CAST(SESSION_CONTEXT(N'user_id') AS UNIQUEIDENTIFIER);
    DECLARE @record_id UNIQUEIDENTIFIER;

    IF EXISTS (SELECT 1 FROM inserted) AND EXISTS (SELECT 1 FROM deleted)
        SET @action = 'UPDATE';
    ELSE IF EXISTS (SELECT 1 FROM inserted)
        SET @action = 'CREATE';
    ELSE
        SET @action = 'DELETE';

    SELECT @record_id = vital_id FROM inserted;
    IF @record_id IS NULL SELECT @record_id = vital_id FROM deleted;

    INSERT INTO audit_logs (log_id, user_id, action, table_affected, record_id, old_value, new_value, timestamp)
    SELECT NEWID(), @user_id, @action, 'vitals', @record_id,
        (SELECT * FROM deleted  FOR JSON PATH),
        (SELECT * FROM inserted FOR JSON PATH),
        GETDATE();
END;
GO

-- prescriptions
DROP TRIGGER IF EXISTS dbo.trg_audit_prescriptions;
GO
CREATE TRIGGER trg_audit_prescriptions
ON prescriptions
AFTER INSERT, UPDATE, DELETE
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @action   NVARCHAR(10);
    DECLARE @user_id  UNIQUEIDENTIFIER = TRY_CAST(SESSION_CONTEXT(N'user_id') AS UNIQUEIDENTIFIER);
    DECLARE @record_id UNIQUEIDENTIFIER;

    IF EXISTS (SELECT 1 FROM inserted) AND EXISTS (SELECT 1 FROM deleted)
        SET @action = 'UPDATE';
    ELSE IF EXISTS (SELECT 1 FROM inserted)
        SET @action = 'CREATE';
    ELSE
        SET @action = 'DELETE';

    SELECT @record_id = prescription_id FROM inserted;
    IF @record_id IS NULL SELECT @record_id = prescription_id FROM deleted;

    INSERT INTO audit_logs (log_id, user_id, action, table_affected, record_id, old_value, new_value, timestamp)
    SELECT NEWID(), @user_id, @action, 'prescriptions', @record_id,
        (SELECT * FROM deleted  FOR JSON PATH),
        (SELECT * FROM inserted FOR JSON PATH),
        GETDATE();
END;
GO

-- lab_orders
DROP TRIGGER IF EXISTS dbo.trg_audit_lab_orders;
GO
CREATE TRIGGER trg_audit_lab_orders
ON lab_orders
AFTER INSERT, UPDATE, DELETE
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @action   NVARCHAR(10);
    DECLARE @user_id  UNIQUEIDENTIFIER = TRY_CAST(SESSION_CONTEXT(N'user_id') AS UNIQUEIDENTIFIER);
    DECLARE @record_id UNIQUEIDENTIFIER;

    IF EXISTS (SELECT 1 FROM inserted) AND EXISTS (SELECT 1 FROM deleted)
        SET @action = 'UPDATE';
    ELSE IF EXISTS (SELECT 1 FROM inserted)
        SET @action = 'CREATE';
    ELSE
        SET @action = 'DELETE';

    SELECT @record_id = order_id FROM inserted;
    IF @record_id IS NULL SELECT @record_id = order_id FROM deleted;

    INSERT INTO audit_logs (log_id, user_id, action, table_affected, record_id, old_value, new_value, timestamp)
    SELECT NEWID(), @user_id, @action, 'lab_orders', @record_id,
        (SELECT * FROM deleted  FOR JSON PATH),
        (SELECT * FROM inserted FOR JSON PATH),
        GETDATE();
END;
GO

-- lab_results
DROP TRIGGER IF EXISTS dbo.trg_audit_lab_results;
GO
CREATE TRIGGER trg_audit_lab_results
ON lab_results
AFTER INSERT, UPDATE, DELETE
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @action   NVARCHAR(10);
    DECLARE @user_id  UNIQUEIDENTIFIER = TRY_CAST(SESSION_CONTEXT(N'user_id') AS UNIQUEIDENTIFIER);
    DECLARE @record_id UNIQUEIDENTIFIER;

    IF EXISTS (SELECT 1 FROM inserted) AND EXISTS (SELECT 1 FROM deleted)
        SET @action = 'UPDATE';
    ELSE IF EXISTS (SELECT 1 FROM inserted)
        SET @action = 'CREATE';
    ELSE
        SET @action = 'DELETE';

    SELECT @record_id = result_id FROM inserted;
    IF @record_id IS NULL SELECT @record_id = result_id FROM deleted;

    INSERT INTO audit_logs (log_id, user_id, action, table_affected, record_id, old_value, new_value, timestamp)
    SELECT NEWID(), @user_id, @action, 'lab_results', @record_id,
        (SELECT * FROM deleted  FOR JSON PATH),
        (SELECT * FROM inserted FOR JSON PATH),
        GETDATE();
END;
GO

-- imaging_records
DROP TRIGGER IF EXISTS dbo.trg_audit_imaging_records;
GO
CREATE TRIGGER trg_audit_imaging_records
ON imaging_records
AFTER INSERT, UPDATE, DELETE
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @action   NVARCHAR(10);
    DECLARE @user_id  UNIQUEIDENTIFIER = TRY_CAST(SESSION_CONTEXT(N'user_id') AS UNIQUEIDENTIFIER);
    DECLARE @record_id UNIQUEIDENTIFIER;

    IF EXISTS (SELECT 1 FROM inserted) AND EXISTS (SELECT 1 FROM deleted)
        SET @action = 'UPDATE';
    ELSE IF EXISTS (SELECT 1 FROM inserted)
        SET @action = 'CREATE';
    ELSE
        SET @action = 'DELETE';

    SELECT @record_id = imaging_id FROM inserted;
    IF @record_id IS NULL SELECT @record_id = imaging_id FROM deleted;

    INSERT INTO audit_logs (log_id, user_id, action, table_affected, record_id, old_value, new_value, timestamp)
    SELECT NEWID(), @user_id, @action, 'imaging_records', @record_id,
        (SELECT * FROM deleted  FOR JSON PATH),
        (SELECT * FROM inserted FOR JSON PATH),
        GETDATE();
END;
GO

-- medical_history
DROP TRIGGER IF EXISTS dbo.trg_audit_medical_history;
GO
CREATE TRIGGER trg_audit_medical_history
ON medical_history
AFTER INSERT, UPDATE, DELETE
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @action   NVARCHAR(10);
    DECLARE @user_id  UNIQUEIDENTIFIER = TRY_CAST(SESSION_CONTEXT(N'user_id') AS UNIQUEIDENTIFIER);
    DECLARE @record_id UNIQUEIDENTIFIER;

    IF EXISTS (SELECT 1 FROM inserted) AND EXISTS (SELECT 1 FROM deleted)
        SET @action = 'UPDATE';
    ELSE IF EXISTS (SELECT 1 FROM inserted)
        SET @action = 'CREATE';
    ELSE
        SET @action = 'DELETE';

    SELECT @record_id = history_id FROM inserted;
    IF @record_id IS NULL SELECT @record_id = history_id FROM deleted;

    INSERT INTO audit_logs (log_id, user_id, action, table_affected, record_id, old_value, new_value, timestamp)
    SELECT NEWID(), @user_id, @action, 'medical_history', @record_id,
        (SELECT * FROM deleted  FOR JSON PATH),
        (SELECT * FROM inserted FOR JSON PATH),
        GETDATE();
END;
GO

-- allergies
DROP TRIGGER IF EXISTS dbo.trg_audit_allergies;
GO
CREATE TRIGGER trg_audit_allergies
ON allergies
AFTER INSERT, UPDATE, DELETE
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @action   NVARCHAR(10);
    DECLARE @user_id  UNIQUEIDENTIFIER = TRY_CAST(SESSION_CONTEXT(N'user_id') AS UNIQUEIDENTIFIER);
    DECLARE @record_id UNIQUEIDENTIFIER;

    IF EXISTS (SELECT 1 FROM inserted) AND EXISTS (SELECT 1 FROM deleted)
        SET @action = 'UPDATE';
    ELSE IF EXISTS (SELECT 1 FROM inserted)
        SET @action = 'CREATE';
    ELSE
        SET @action = 'DELETE';

    SELECT @record_id = allergy_id FROM inserted;
    IF @record_id IS NULL SELECT @record_id = allergy_id FROM deleted;

    INSERT INTO audit_logs (log_id, user_id, action, table_affected, record_id, old_value, new_value, timestamp)
    SELECT NEWID(), @user_id, @action, 'allergies', @record_id,
        (SELECT * FROM deleted  FOR JSON PATH),
        (SELECT * FROM inserted FOR JSON PATH),
        GETDATE();
END;
GO

-- vaccinations
DROP TRIGGER IF EXISTS dbo.trg_audit_vaccinations;
GO
CREATE TRIGGER trg_audit_vaccinations
ON vaccinations
AFTER INSERT, UPDATE, DELETE
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @action   NVARCHAR(10);
    DECLARE @user_id  UNIQUEIDENTIFIER = TRY_CAST(SESSION_CONTEXT(N'user_id') AS UNIQUEIDENTIFIER);
    DECLARE @record_id UNIQUEIDENTIFIER;

    IF EXISTS (SELECT 1 FROM inserted) AND EXISTS (SELECT 1 FROM deleted)
        SET @action = 'UPDATE';
    ELSE IF EXISTS (SELECT 1 FROM inserted)
        SET @action = 'CREATE';
    ELSE
        SET @action = 'DELETE';

    SELECT @record_id = vaccination_id FROM inserted;
    IF @record_id IS NULL SELECT @record_id = vaccination_id FROM deleted;

    INSERT INTO audit_logs (log_id, user_id, action, table_affected, record_id, old_value, new_value, timestamp)
    SELECT NEWID(), @user_id, @action, 'vaccinations', @record_id,
        (SELECT * FROM deleted  FOR JSON PATH),
        (SELECT * FROM inserted FOR JSON PATH),
        GETDATE();
END;
GO

-- referrals
DROP TRIGGER IF EXISTS dbo.trg_audit_referrals;
GO
CREATE TRIGGER trg_audit_referrals
ON referrals
AFTER INSERT, UPDATE, DELETE
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @action   NVARCHAR(10);
    DECLARE @user_id  UNIQUEIDENTIFIER = TRY_CAST(SESSION_CONTEXT(N'user_id') AS UNIQUEIDENTIFIER);
    DECLARE @record_id UNIQUEIDENTIFIER;

    IF EXISTS (SELECT 1 FROM inserted) AND EXISTS (SELECT 1 FROM deleted)
        SET @action = 'UPDATE';
    ELSE IF EXISTS (SELECT 1 FROM inserted)
        SET @action = 'CREATE';
    ELSE
        SET @action = 'DELETE';

    SELECT @record_id = referral_id FROM inserted;
    IF @record_id IS NULL SELECT @record_id = referral_id FROM deleted;

    INSERT INTO audit_logs (log_id, user_id, action, table_affected, record_id, old_value, new_value, timestamp)
    SELECT NEWID(), @user_id, @action, 'referrals', @record_id,
        (SELECT * FROM deleted  FOR JSON PATH),
        (SELECT * FROM inserted FOR JSON PATH),
        GETDATE();
END;
GO

-- care_plans
DROP TRIGGER IF EXISTS dbo.trg_audit_care_plans;
GO
CREATE TRIGGER trg_audit_care_plans
ON care_plans
AFTER INSERT, UPDATE, DELETE
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @action   NVARCHAR(10);
    DECLARE @user_id  UNIQUEIDENTIFIER = TRY_CAST(SESSION_CONTEXT(N'user_id') AS UNIQUEIDENTIFIER);
    DECLARE @record_id UNIQUEIDENTIFIER;

    IF EXISTS (SELECT 1 FROM inserted) AND EXISTS (SELECT 1 FROM deleted)
        SET @action = 'UPDATE';
    ELSE IF EXISTS (SELECT 1 FROM inserted)
        SET @action = 'CREATE';
    ELSE
        SET @action = 'DELETE';

    SELECT @record_id = plan_id FROM inserted;
    IF @record_id IS NULL SELECT @record_id = plan_id FROM deleted;

    INSERT INTO audit_logs (log_id, user_id, action, table_affected, record_id, old_value, new_value, timestamp)
    SELECT NEWID(), @user_id, @action, 'care_plans', @record_id,
        (SELECT * FROM deleted  FOR JSON PATH),
        (SELECT * FROM inserted FOR JSON PATH),
        GETDATE();
END;
GO


-- ============================================================
-- B. trg_calculate_bmi
-- Auto-calculates BMI after vitals INSERT or UPDATE.
-- Formula: weight_kg / (height_cm / 100)^2
-- ============================================================
DROP TRIGGER IF EXISTS dbo.trg_calculate_bmi;
GO
CREATE TRIGGER trg_calculate_bmi
ON vitals
AFTER INSERT, UPDATE
AS
BEGIN
    SET NOCOUNT ON;

    UPDATE v
    SET bmi = ROUND(
        i.weight_kg / POWER(i.height_cm / 100.0, 2), 2
    )
    FROM vitals v
    INNER JOIN inserted i ON v.vital_id = i.vital_id
    WHERE i.weight_kg IS NOT NULL
      AND i.height_cm IS NOT NULL
      AND i.height_cm > 0;
END;
GO


-- ============================================================
-- C. trg_flag_abnormal_vitals
-- Sets is_abnormal = 1 on INSERT if any vital is outside range.
-- ============================================================
DROP TRIGGER IF EXISTS dbo.trg_flag_abnormal_vitals;
GO
CREATE TRIGGER trg_flag_abnormal_vitals
ON vitals
AFTER INSERT
AS
BEGIN
    SET NOCOUNT ON;

    UPDATE v
    SET is_abnormal = 1
    FROM vitals v
    INNER JOIN inserted i ON v.vital_id = i.vital_id
    WHERE i.heart_rate         > 100
       OR i.heart_rate         < 60
       OR i.blood_pressure_sys > 140
       OR i.blood_pressure_sys < 90
       OR i.blood_pressure_dia > 90
       OR i.oxygen_saturation  < 95
       OR i.temperature        > 37.5
       OR i.temperature        < 36.0
       OR i.respiratory_rate   > 20
       OR i.respiratory_rate   < 12;
END;
GO

PRINT 'All triggers created.';
