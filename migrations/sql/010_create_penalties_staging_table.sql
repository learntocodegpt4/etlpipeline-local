-- Migration: 010_create_penalties_staging_table.sql
-- Creates the staging table for FWC Penalties data
-- Run against MS SQL Server

-- Penalties staging table
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Stg_TblPenalties' AND xtype='U')
CREATE TABLE Stg_TblPenalties (
    id INT IDENTITY(1,1) PRIMARY KEY,
    penalty_fixed_id INT NOT NULL,
    award_code NVARCHAR(50) NOT NULL,
    clause_fixed_id INT NULL,
    clause_description NVARCHAR(2000) NULL,
    classification_level INT NULL,
    penalty_description NVARCHAR(1000) NULL,
    rate DECIMAL(18,2) NULL,
    employee_rate_type_code NVARCHAR(20) NULL,
    penalty_calculated_value DECIMAL(18,4) NULL,
    calculated_includes_all_purpose BIT NULL,
    base_pay_rate_id NVARCHAR(50) NULL,
    operative_from DATETIME2 NULL,
    operative_to DATETIME2 NULL,
    version_number INT NULL,
    last_modified_datetime DATETIME2 NULL,
    published_year INT NULL,
    created_at DATETIME2 DEFAULT GETUTCDATE(),
    updated_at DATETIME2 DEFAULT GETUTCDATE()
);
GO

-- Create indexes for better query performance
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name='ix_stg_tblpenalties_award' AND object_id = OBJECT_ID('Stg_TblPenalties'))
CREATE INDEX ix_stg_tblpenalties_award ON Stg_TblPenalties(award_code);
GO

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name='ix_stg_tblpenalties_award_year' AND object_id = OBJECT_ID('Stg_TblPenalties'))
CREATE INDEX ix_stg_tblpenalties_award_year ON Stg_TblPenalties(award_code, published_year);
GO

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name='ix_stg_tblpenalties_penalty_id' AND object_id = OBJECT_ID('Stg_TblPenalties'))
CREATE INDEX ix_stg_tblpenalties_penalty_id ON Stg_TblPenalties(penalty_fixed_id);
GO

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name='ix_stg_tblpenalties_classification_level' AND object_id = OBJECT_ID('Stg_TblPenalties'))
CREATE INDEX ix_stg_tblpenalties_classification_level ON Stg_TblPenalties(classification_level);
GO

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name='ix_stg_tblpenalties_base_pay_rate' AND object_id = OBJECT_ID('Stg_TblPenalties'))
CREATE INDEX ix_stg_tblpenalties_base_pay_rate ON Stg_TblPenalties(base_pay_rate_id);
GO
