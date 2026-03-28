USE pdms_db;
GO

-- ============================================================
-- STORED PROCEDURES
-- Run order: 11 — run after all tables and triggers (01–10)
--
-- Procedures:
--   usp_create_encounter    — opens a new clinical encounter (ACID)
--   usp_record_prescription — issues a prescription with allergy check (ACID)
--
-- Calling from Python (SQLAlchemy + pyodbc):
--   Both procedures use OUTPUT parameters.
--   See comments at the bottom of each procedure for Python examples.
-- ============================================================


-- ============================================================
-- usp_create_encounter
-- ============================================================
DROP PROCEDURE IF EXISTS dbo.usp_create_encounter;
GO
CREATE PROCEDURE usp_create_encounter
    @p_patient_id      UNIQUEIDENTIFIER,
    @p_doctor_id       UNIQUEIDENTIFIER,
    @p_appointment_id  UNIQUEIDENTIFIER = NULL,
    @p_encounter_type  NVARCHAR(20),
    @p_chief_complaint NVARCHAR(MAX),
    @p_created_by      UNIQUEIDENTIFIER,
    @p_encounter_id    UNIQUEIDENTIFIER OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRANSACTION;
    BEGIN TRY

        -- Step 1: Validate encounter type
        IF @p_encounter_type NOT IN ('outpatient', 'follow-up', 'emergency')
        BEGIN
            RAISERROR('INVALID_TYPE: encounter_type must be outpatient, follow-up, or emergency.', 16, 1);
            RETURN;
        END

        -- Step 2: Generate new encounter ID
        SET @p_encounter_id = NEWID();

        -- Step 3: Calculate visit number for this patient
        DECLARE @visit_number INT;
        SELECT @visit_number = COUNT(*) + 1
        FROM encounters
        WHERE patient_id = @p_patient_id;

        -- Step 4: Insert encounter
        INSERT INTO encounters (
            encounter_id, patient_id, doctor_id,
            appointment_id, encounter_type,
            chief_complaint, status,
            visit_number, created_at
        )
        VALUES (
            @p_encounter_id, @p_patient_id, @p_doctor_id,
            @p_appointment_id, @p_encounter_type,
            @p_chief_complaint, 'open',
            @visit_number, GETDATE()
        );

        -- Step 5: Update linked appointment to 'completed' if provided
        IF @p_appointment_id IS NOT NULL
        BEGIN
            UPDATE appointments
            SET status = 'completed'
            WHERE appointment_id = @p_appointment_id
              AND status != 'cancelled';
        END

        -- Step 6: Insert empty SOAP note shell (doctor fills it in later)
        INSERT INTO clinical_notes (
            note_id, encounter_id, doctor_id, recorded_at
        )
        VALUES (
            NEWID(), @p_encounter_id, @p_doctor_id, GETDATE()
        );

        -- Step 7: Write audit log
        INSERT INTO audit_logs (
            log_id, user_id, action,
            module, table_affected, record_id, timestamp
        )
        VALUES (
            NEWID(), @p_created_by, 'CREATE',
            'encounters', 'encounters', @p_encounter_id, GETDATE()
        );

        COMMIT TRANSACTION;

    END TRY
    BEGIN CATCH
        ROLLBACK TRANSACTION;
        THROW;
    END CATCH
END;
GO

-- Python usage example:
-- from sqlalchemy import text
--
-- def create_encounter(db, patient_id, doctor_id, enc_type, complaint, created_by):
--     sql = text("""
--         DECLARE @new_id UNIQUEIDENTIFIER;
--         EXEC usp_create_encounter
--             @p_patient_id      = :patient_id,
--             @p_doctor_id       = :doctor_id,
--             @p_encounter_type  = :enc_type,
--             @p_chief_complaint = :complaint,
--             @p_created_by      = :created_by,
--             @p_encounter_id    = @new_id OUTPUT;
--         SELECT @new_id AS encounter_id;
--     """)
--     result = db.execute(sql, {
--         "patient_id": str(patient_id), "doctor_id": str(doctor_id),
--         "enc_type": enc_type, "complaint": complaint,
--         "created_by": str(created_by)
--     })
--     return result.scalar()


-- ============================================================
-- usp_record_prescription
-- ============================================================
DROP PROCEDURE IF EXISTS dbo.usp_record_prescription;
GO
CREATE PROCEDURE usp_record_prescription
    @p_encounter_id    UNIQUEIDENTIFIER,
    @p_patient_id      UNIQUEIDENTIFIER,
    @p_doctor_id       UNIQUEIDENTIFIER,
    @p_drug_name       NVARCHAR(200),
    @p_dosage          NVARCHAR(50),
    @p_frequency       NVARCHAR(50),
    @p_duration        NVARCHAR(50),
    @p_route           NVARCHAR(30),
    @p_instructions    NVARCHAR(MAX),
    @p_prescription_id UNIQUEIDENTIFIER OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRANSACTION;
    BEGIN TRY

        -- Step 1: Verify the encounter is still open
        IF NOT EXISTS (
            SELECT 1 FROM encounters
            WHERE encounter_id = @p_encounter_id
              AND status = 'open'
        )
        BEGIN
            RAISERROR('ENCOUNTER_CLOSED: Cannot prescribe on a closed encounter.', 16, 1);
            RETURN;
        END

        -- Step 2: Check patient allergies (exact case-insensitive match)
        IF EXISTS (
            SELECT 1 FROM allergies
            WHERE patient_id = @p_patient_id
              AND is_removed  = 0
              AND LOWER(allergen) = LOWER(@p_drug_name)
        )
        BEGIN
            RAISERROR('ALLERGY_CONFLICT: Patient is allergic to %s.', 16, 1, @p_drug_name);
            RETURN;
        END

        -- Step 3: Insert prescription
        SET @p_prescription_id = NEWID();

        INSERT INTO prescriptions (
            prescription_id, encounter_id, patient_id,
            doctor_id, drug_name, dosage, frequency,
            duration, route, instructions,
            is_active, issued_at
        )
        VALUES (
            @p_prescription_id, @p_encounter_id, @p_patient_id,
            @p_doctor_id, @p_drug_name, @p_dosage, @p_frequency,
            @p_duration, @p_route, @p_instructions,
            1, GETDATE()
        );

        -- Step 4: Write audit log
        INSERT INTO audit_logs (
            log_id, user_id, action,
            module, table_affected, record_id, timestamp
        )
        VALUES (
            NEWID(), @p_doctor_id, 'CREATE',
            'prescriptions', 'prescriptions', @p_prescription_id, GETDATE()
        );

        COMMIT TRANSACTION;

    END TRY
    BEGIN CATCH
        ROLLBACK TRANSACTION;
        THROW;
    END CATCH
END;
GO

PRINT 'All stored procedures created.';
