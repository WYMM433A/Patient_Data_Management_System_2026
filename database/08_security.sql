USE pdms_db;
GO

-- ============================================================
-- MODULE: SECURITY / AUDIT
-- Tables: audit_logs
-- Run order: 08 — depends on 01 (users)
-- Rules:
--   - NO UPDATE or DELETE endpoint ever touches this table
--   - INSERT-only: populated by SQL Server triggers (data mutations)
--     and by app middleware (VIEW actions)
--   - old_value / new_value stored as JSON (via FOR JSON PATH)
--   - user_id for trigger-generated rows comes from SESSION_CONTEXT
--     set by the FastAPI app before executing queries:
--       EXEC sys.sp_set_session_context @key=N'user_id', @value='<uuid>'
-- ============================================================

-- 22. AUDIT_LOGS
IF OBJECT_ID('dbo.audit_logs', 'U') IS NULL
BEGIN
    CREATE TABLE audit_logs (
        log_id         UNIQUEIDENTIFIER  NOT NULL CONSTRAINT PK_audit_logs PRIMARY KEY DEFAULT NEWID(),
        user_id        UNIQUEIDENTIFIER,            -- NULL if triggered before session is set
        action         NVARCHAR(20)      NOT NULL
                           CONSTRAINT CHK_audit_action
                               CHECK (action IN ('CREATE', 'UPDATE', 'DELETE', 'VIEW')),
        module         NVARCHAR(50),
        table_affected NVARCHAR(100),
        record_id      UNIQUEIDENTIFIER,
        old_value      NVARCHAR(MAX),               -- JSON via FOR JSON PATH (UPDATE/DELETE)
        new_value      NVARCHAR(MAX),               -- JSON via FOR JSON PATH (INSERT/UPDATE)
        ip_address     NVARCHAR(45),                -- supports IPv6
        user_agent     NVARCHAR(500),
        timestamp      DATETIME2         NOT NULL DEFAULT GETDATE(),
        CONSTRAINT FK_audit_user FOREIGN KEY (user_id) REFERENCES users(user_id)
    );
    PRINT 'Table audit_logs created.';
END
ELSE
    PRINT 'Table audit_logs already exists — skipped.';
GO
