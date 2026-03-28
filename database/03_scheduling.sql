USE pdms_db;
GO

-- ============================================================
-- MODULE: SCHEDULING
-- Tables: appointments
-- Run order: 03 — depends on 01 (users), 02 (patients)
-- ============================================================

-- 9. APPOINTMENTS
IF OBJECT_ID('dbo.appointments', 'U') IS NULL
BEGIN
    CREATE TABLE appointments (
        appointment_id UNIQUEIDENTIFIER  NOT NULL CONSTRAINT PK_appointments PRIMARY KEY DEFAULT NEWID(),
        patient_id     UNIQUEIDENTIFIER  NOT NULL,
        doctor_id      UNIQUEIDENTIFIER  NOT NULL,
        scheduled_at   DATETIME2         NOT NULL,
        reason         NVARCHAR(MAX),
        status         NVARCHAR(20)      NOT NULL DEFAULT 'scheduled'
                           CONSTRAINT CHK_appt_status
                               CHECK (status IN ('scheduled', 'confirmed', 'completed', 'cancelled')),
        notes          NVARCHAR(MAX),
        created_by     UNIQUEIDENTIFIER  NOT NULL,
        created_at     DATETIME2         NOT NULL DEFAULT GETDATE(),
        CONSTRAINT FK_appt_patient    FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
        CONSTRAINT FK_appt_doctor     FOREIGN KEY (doctor_id)  REFERENCES users(user_id),
        CONSTRAINT FK_appt_created_by FOREIGN KEY (created_by) REFERENCES users(user_id)
    );
    PRINT 'Table appointments created.';
END
ELSE
    PRINT 'Table appointments already exists — skipped.';
GO
