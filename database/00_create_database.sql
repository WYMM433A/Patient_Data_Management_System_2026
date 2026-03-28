-- Run this in SSMS connected to localhost
-- Creates the pdms_db database for local development

IF NOT EXISTS (
    SELECT name FROM sys.databases WHERE name = 'pdms_db'
)
BEGIN
    CREATE DATABASE pdms_db;
    PRINT 'pdms_db created successfully.';
END
ELSE
BEGIN
    PRINT 'pdms_db already exists.';
END
