USE pdms_db;
GO

-- ============================================================
-- MODULE: CARE COORDINATION
-- Tables: referrals, care_plans
-- Run order: 07 — depends on 01 (users), 02 (patients), 04 (encounters)
-- ============================================================

-- 20. REFERRALS
IF OBJECT_ID('dbo.referrals', 'U') IS NULL
BEGIN
    CREATE TABLE referrals (
        referral_id  UNIQUEIDENTIFIER  NOT NULL CONSTRAINT PK_referrals PRIMARY KEY DEFAULT NEWID(),
        encounter_id UNIQUEIDENTIFIER  NOT NULL,
        patient_id   UNIQUEIDENTIFIER  NOT NULL,
        referred_by  UNIQUEIDENTIFIER  NOT NULL,
        specialty    NVARCHAR(100)     NOT NULL,
        reason       NVARCHAR(MAX),
        urgency      NVARCHAR(20)      NOT NULL DEFAULT 'routine'
                         CONSTRAINT CHK_referral_urgency
                             CHECK (urgency IN ('routine', 'urgent')),
        status       NVARCHAR(20)      NOT NULL DEFAULT 'pending'
                         CONSTRAINT CHK_referral_status
                             CHECK (status IN ('pending', 'accepted', 'completed')),
        referred_at  DATETIME2         NOT NULL DEFAULT GETDATE(),
        event_date   DATETIME2,
        CONSTRAINT FK_ref_encounter FOREIGN KEY (encounter_id) REFERENCES encounters(encounter_id),
        CONSTRAINT FK_ref_patient   FOREIGN KEY (patient_id)   REFERENCES patients(patient_id),
        CONSTRAINT FK_ref_by        FOREIGN KEY (referred_by)  REFERENCES users(user_id)
    );
    PRINT 'Table referrals created.';
END
ELSE
    PRINT 'Table referrals already exists — skipped.';
GO

-- 21. CARE_PLANS
-- Used for chronic disease management (diabetes, hypertension, etc.)
IF OBJECT_ID('dbo.care_plans', 'U') IS NULL
BEGIN
    CREATE TABLE care_plans (
        plan_id       UNIQUEIDENTIFIER  NOT NULL CONSTRAINT PK_care_plans PRIMARY KEY DEFAULT NEWID(),
        patient_id    UNIQUEIDENTIFIER  NOT NULL,
        doctor_id     UNIQUEIDENTIFIER  NOT NULL,
        condition     NVARCHAR(200)     NOT NULL,
        goals         NVARCHAR(MAX),
        interventions NVARCHAR(MAX),
        start_date    DATE              NOT NULL,
        review_date   DATE,
        status        NVARCHAR(20)      NOT NULL DEFAULT 'active'
                          CONSTRAINT CHK_plan_status
                              CHECK (status IN ('active', 'completed', 'cancelled')),
        notes         NVARCHAR(MAX),
        created_at    DATETIME2         NOT NULL DEFAULT GETDATE(),
        updated_at    DATETIME2,
        CONSTRAINT FK_plan_patient FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
        CONSTRAINT FK_plan_doctor  FOREIGN KEY (doctor_id)  REFERENCES users(user_id)
    );
    PRINT 'Table care_plans created.';
END
ELSE
    PRINT 'Table care_plans already exists — skipped.';
GO
