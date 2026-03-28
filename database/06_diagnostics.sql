USE pdms_db;
GO

-- ============================================================
-- MODULE: DIAGNOSTICS
-- Tables: lab_test_templates, lab_test_parameters,
--         lab_orders, lab_results, imaging_records
-- Run order: 06 — depends on 01 (users), 02 (patients), 04 (encounters)
-- ============================================================

-- 16. LAB_TEST_TEMPLATES
-- Master list of available lab test types (e.g. CBC, LFT, HbA1c).
-- Seeded in 12_seed.sql.
IF OBJECT_ID('dbo.lab_test_templates', 'U') IS NULL
BEGIN
    CREATE TABLE lab_test_templates (
        template_id   UNIQUEIDENTIFIER  NOT NULL CONSTRAINT PK_lab_test_templates PRIMARY KEY DEFAULT NEWID(),
        test_name     NVARCHAR(200)     NOT NULL,
        test_code     NVARCHAR(20)      NOT NULL CONSTRAINT UQ_template_code UNIQUE,
        test_category NVARCHAR(50)      NOT NULL,
        description   NVARCHAR(MAX),
        is_active     BIT               NOT NULL DEFAULT 1
    );
    PRINT 'Table lab_test_templates created.';
END
ELSE
    PRINT 'Table lab_test_templates already exists — skipped.';
GO

-- 17. LAB_TEST_PARAMETERS
-- Each row is one reportable parameter within a test template.
-- Controls the dynamic form rendered for lab technicians.
IF OBJECT_ID('dbo.lab_test_parameters', 'U') IS NULL
BEGIN
    CREATE TABLE lab_test_parameters (
        parameter_id      UNIQUEIDENTIFIER  NOT NULL CONSTRAINT PK_lab_test_parameters PRIMARY KEY DEFAULT NEWID(),
        template_id       UNIQUEIDENTIFIER  NOT NULL,
        parameter_name    NVARCHAR(100)     NOT NULL,
        display_order     INT               NOT NULL,
        unit              NVARCHAR(30),
        normal_range_min  DECIMAL(10,3),
        normal_range_max  DECIMAL(10,3),
        normal_range_text NVARCHAR(100),   -- for text results like "Negative", "Below 5.7"
        value_type        NVARCHAR(20)      NOT NULL DEFAULT 'numeric'
                              CONSTRAINT CHK_param_value_type
                                  CHECK (value_type IN ('numeric', 'text', 'positive_negative')),
        is_required       BIT               NOT NULL DEFAULT 1,
        CONSTRAINT FK_param_template FOREIGN KEY (template_id) REFERENCES lab_test_templates(template_id)
    );
    PRINT 'Table lab_test_parameters created.';
END
ELSE
    PRINT 'Table lab_test_parameters already exists — skipped.';
GO

-- 15. LAB_ORDERS
-- Created by doctor when ordering a lab test for a patient.
-- template_id links to the dynamic form definition.
IF OBJECT_ID('dbo.lab_orders', 'U') IS NULL
BEGIN
    CREATE TABLE lab_orders (
        order_id      UNIQUEIDENTIFIER  NOT NULL CONSTRAINT PK_lab_orders PRIMARY KEY DEFAULT NEWID(),
        encounter_id  UNIQUEIDENTIFIER  NOT NULL,
        patient_id    UNIQUEIDENTIFIER  NOT NULL,
        ordered_by    UNIQUEIDENTIFIER  NOT NULL,
        template_id   UNIQUEIDENTIFIER,             -- FK to lab_test_templates for dynamic form
        test_name     NVARCHAR(200)     NOT NULL,   -- denormalized copy for display
        test_code     NVARCHAR(20),                 -- denormalized copy (e.g. 'CBC')
        test_category NVARCHAR(100)
                          CONSTRAINT CHK_order_category
                              CHECK (test_category IN (
                                  'hematology', 'biochemistry', 'microbiology',
                                  'serology', 'urinalysis', 'imaging')),
        priority      NVARCHAR(20)      NOT NULL DEFAULT 'routine'
                          CONSTRAINT CHK_order_priority
                              CHECK (priority IN ('routine', 'urgent', 'stat')),
        status        NVARCHAR(20)      NOT NULL DEFAULT 'ordered'
                          CONSTRAINT CHK_order_status
                              CHECK (status IN ('ordered', 'in-progress', 'completed')),
        ordered_at    DATETIME2         NOT NULL DEFAULT GETDATE(),
        event_date    DATETIME2,
        CONSTRAINT FK_order_encounter FOREIGN KEY (encounter_id) REFERENCES encounters(encounter_id),
        CONSTRAINT FK_order_patient   FOREIGN KEY (patient_id)   REFERENCES patients(patient_id),
        CONSTRAINT FK_order_by        FOREIGN KEY (ordered_by)   REFERENCES users(user_id),
        CONSTRAINT FK_order_template  FOREIGN KEY (template_id)  REFERENCES lab_test_templates(template_id)
    );
    PRINT 'Table lab_orders created.';
END
ELSE
    PRINT 'Table lab_orders already exists — skipped.';
GO

-- 18. LAB_RESULTS
-- One row per parameter per order (populated when lab tech submits results).
-- is_abnormal is set by comparing result_value against normal_range_min/max.
IF OBJECT_ID('dbo.lab_results', 'U') IS NULL
BEGIN
    CREATE TABLE lab_results (
        result_id      UNIQUEIDENTIFIER  NOT NULL CONSTRAINT PK_lab_results PRIMARY KEY DEFAULT NEWID(),
        order_id       UNIQUEIDENTIFIER  NOT NULL,
        patient_id     UNIQUEIDENTIFIER  NOT NULL,
        parameter_id   UNIQUEIDENTIFIER,             -- links to template parameter
        uploaded_by    UNIQUEIDENTIFIER  NOT NULL,
        parameter_name NVARCHAR(100)     NOT NULL,   -- denormalized copy for quick display
        result_value   NVARCHAR(100)     NOT NULL,
        unit           NVARCHAR(30),
        normal_range   NVARCHAR(100),                -- denormalized copy for quick display
        is_abnormal    BIT               NOT NULL DEFAULT 0,
        abnormal_level NVARCHAR(20)
                           CONSTRAINT CHK_result_abnormal_level
                               CHECK (abnormal_level IN ('low', 'borderline', 'high', 'critical')),
        notes          NVARCHAR(MAX),
        result_file_url NVARCHAR(500),
        resulted_at    DATETIME2         NOT NULL DEFAULT GETDATE(),
        validated_at   DATETIME2,
        validated_by   UNIQUEIDENTIFIER,
        CONSTRAINT FK_result_order      FOREIGN KEY (order_id)     REFERENCES lab_orders(order_id),
        CONSTRAINT FK_result_patient    FOREIGN KEY (patient_id)   REFERENCES patients(patient_id),
        CONSTRAINT FK_result_parameter  FOREIGN KEY (parameter_id) REFERENCES lab_test_parameters(parameter_id),
        CONSTRAINT FK_result_uploaded   FOREIGN KEY (uploaded_by)  REFERENCES users(user_id),
        CONSTRAINT FK_result_validated  FOREIGN KEY (validated_by) REFERENCES users(user_id)
    );
    PRINT 'Table lab_results created.';
END
ELSE
    PRINT 'Table lab_results already exists — skipped.';
GO

-- 19. IMAGING_RECORDS
IF OBJECT_ID('dbo.imaging_records', 'U') IS NULL
BEGIN
    CREATE TABLE imaging_records (
        imaging_id        UNIQUEIDENTIFIER  NOT NULL CONSTRAINT PK_imaging_records PRIMARY KEY DEFAULT NEWID(),
        patient_id        UNIQUEIDENTIFIER  NOT NULL,
        encounter_id      UNIQUEIDENTIFIER  NOT NULL,
        ordered_by        UNIQUEIDENTIFIER  NOT NULL,
        imaging_type      NVARCHAR(50)
                              CONSTRAINT CHK_imaging_type
                                  CHECK (imaging_type IN ('X-ray', 'Ultrasound', 'MRI', 'CT', 'ECG')),
        body_part         NVARCHAR(100),
        findings          NVARCHAR(MAX),
        image_url         NVARCHAR(500),
        radiologist_notes NVARCHAR(MAX),
        performed_at      DATETIME2         NOT NULL DEFAULT GETDATE(),
        event_date        DATETIME2,
        validated_at      DATETIME2,
        CONSTRAINT FK_img_patient   FOREIGN KEY (patient_id)   REFERENCES patients(patient_id),
        CONSTRAINT FK_img_encounter FOREIGN KEY (encounter_id) REFERENCES encounters(encounter_id),
        CONSTRAINT FK_img_ordered   FOREIGN KEY (ordered_by)   REFERENCES users(user_id)
    );
    PRINT 'Table imaging_records created.';
END
ELSE
    PRINT 'Table imaging_records already exists — skipped.';
GO
