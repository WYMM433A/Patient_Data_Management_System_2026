USE pdms_db;
GO

-- ============================================================
-- MODULE: RBAC
-- Tables: roles, permissions, role_permissions, users
-- Run order: 01 — no dependencies
-- ============================================================

-- 1. ROLES
IF OBJECT_ID('dbo.roles', 'U') IS NULL
BEGIN
    CREATE TABLE roles (
        role_id     UNIQUEIDENTIFIER  NOT NULL CONSTRAINT PK_roles PRIMARY KEY DEFAULT NEWID(),
        role_name   NVARCHAR(50)      NOT NULL CONSTRAINT UQ_roles_name UNIQUE,
        description NVARCHAR(MAX),
        created_at  DATETIME2         NOT NULL DEFAULT GETDATE()
    );
    PRINT 'Table roles created.';
END
ELSE
    PRINT 'Table roles already exists — skipped.';
GO

-- 2. PERMISSIONS
IF OBJECT_ID('dbo.permissions', 'U') IS NULL
BEGIN
    CREATE TABLE permissions (
        permission_id   UNIQUEIDENTIFIER  NOT NULL CONSTRAINT PK_permissions PRIMARY KEY DEFAULT NEWID(),
        permission_name NVARCHAR(100)     NOT NULL CONSTRAINT UQ_permissions_name UNIQUE,
        module          NVARCHAR(50)      NOT NULL,
        action          NVARCHAR(20)      NOT NULL,
        description     NVARCHAR(MAX)
    );
    PRINT 'Table permissions created.';
END
ELSE
    PRINT 'Table permissions already exists — skipped.';
GO

-- 3. ROLE_PERMISSIONS (junction table)
IF OBJECT_ID('dbo.role_permissions', 'U') IS NULL
BEGIN
    CREATE TABLE role_permissions (
        role_id       UNIQUEIDENTIFIER  NOT NULL,
        permission_id UNIQUEIDENTIFIER  NOT NULL,
        CONSTRAINT PK_role_permissions     PRIMARY KEY (role_id, permission_id),
        CONSTRAINT FK_rp_role              FOREIGN KEY (role_id)
            REFERENCES roles(role_id),
        CONSTRAINT FK_rp_permission        FOREIGN KEY (permission_id)
            REFERENCES permissions(permission_id)
    );
    PRINT 'Table role_permissions created.';
END
ELSE
    PRINT 'Table role_permissions already exists — skipped.';
GO

-- 4. USERS
IF OBJECT_ID('dbo.users', 'U') IS NULL
BEGIN
    CREATE TABLE users (
        user_id       UNIQUEIDENTIFIER  NOT NULL CONSTRAINT PK_users PRIMARY KEY DEFAULT NEWID(),
        username      NVARCHAR(100)     NOT NULL CONSTRAINT UQ_users_username UNIQUE,
        password_hash NVARCHAR(255)     NOT NULL,
        email         NVARCHAR(150)     NOT NULL CONSTRAINT UQ_users_email UNIQUE,
        role_id       UNIQUEIDENTIFIER  NOT NULL,
        first_name    NVARCHAR(100)     NOT NULL,
        last_name     NVARCHAR(100)     NOT NULL,
        is_active     BIT               NOT NULL DEFAULT 1,
        created_at    DATETIME2         NOT NULL DEFAULT GETDATE(),
        last_login    DATETIME2,
        CONSTRAINT FK_users_role FOREIGN KEY (role_id)
            REFERENCES roles(role_id)
    );
    PRINT 'Table users created.';
END
ELSE
    PRINT 'Table users already exists — skipped.';
GO
