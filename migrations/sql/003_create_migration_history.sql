-- Migration: 003_create_migration_history.sql
-- Creates migration tracking table

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Tblmigration_history' AND xtype='U')
CREATE TABLE Tblmigration_history (
    id INT IDENTITY(1,1) PRIMARY KEY,
    migration_name NVARCHAR(200) NOT NULL UNIQUE,
    applied_at DATETIME2 DEFAULT GETUTCDATE(),
    checksum NVARCHAR(64) NULL
);
GO

-- Insert migration records
IF NOT EXISTS (SELECT 1 FROM Tblmigration_history WHERE migration_name = '001_create_base_tables')
INSERT INTO Tblmigration_history (migration_name) VALUES ('001_create_base_tables');
GO

IF NOT EXISTS (SELECT 1 FROM Tblmigration_history WHERE migration_name = '002_create_etl_tracking_tables')
INSERT INTO Tblmigration_history (migration_name) VALUES ('002_create_etl_tracking_tables');
GO

IF NOT EXISTS (SELECT 1 FROM Tblmigration_history WHERE migration_name = '003_create_migration_history')
INSERT INTO Tblmigration_history (migration_name) VALUES ('003_create_migration_history');
GO

PRINT 'Migration history table created successfully';
GO
