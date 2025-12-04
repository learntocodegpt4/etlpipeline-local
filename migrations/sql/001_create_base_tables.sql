-- Migration: 001_create_base_tables.sql
-- Creates the base database tables for ETL Pipeline
-- Run against MS SQL Server

-- Create database if not exists (run separately with admin privileges)
-- CREATE DATABASE etl_pipeline;
-- GO
-- USE etl_pipeline;
-- GO

-- Awards table
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='awards' AND xtype='U')
CREATE TABLE awards (
    id INT IDENTITY(1,1) PRIMARY KEY,
    award_id INT NOT NULL,
    award_fixed_id INT NOT NULL,
    code NVARCHAR(50) NOT NULL,
    name NVARCHAR(500) NULL,
    award_operative_from DATETIME2 NULL,
    award_operative_to DATETIME2 NULL,
    version_number INT NULL,
    last_modified_datetime DATETIME2 NULL,
    published_year INT NULL,
    created_at DATETIME2 DEFAULT GETUTCDATE(),
    updated_at DATETIME2 DEFAULT GETUTCDATE()
);
GO

CREATE INDEX IF NOT EXISTS ix_awards_code ON awards(code);
GO

CREATE INDEX IF NOT EXISTS ix_awards_code_year ON awards(code, published_year);
GO

-- Classifications table
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='classifications' AND xtype='U')
CREATE TABLE classifications (
    id INT IDENTITY(1,1) PRIMARY KEY,
    classification_fixed_id INT NOT NULL,
    award_code NVARCHAR(50) NOT NULL,
    clause_fixed_id INT NULL,
    clauses NVARCHAR(200) NULL,
    clause_description NVARCHAR(1000) NULL,
    parent_classification_name NVARCHAR(500) NULL,
    classification NVARCHAR(500) NULL,
    classification_level INT NULL,
    next_down_classification_fixed_id INT NULL,
    next_up_classification_fixed_id INT NULL,
    operative_from DATETIME2 NULL,
    operative_to DATETIME2 NULL,
    version_number INT NULL,
    last_modified_datetime DATETIME2 NULL,
    published_year INT NULL,
    created_at DATETIME2 DEFAULT GETUTCDATE(),
    updated_at DATETIME2 DEFAULT GETUTCDATE()
);
GO

CREATE INDEX IF NOT EXISTS ix_classifications_award ON classifications(award_code);
GO

CREATE INDEX IF NOT EXISTS ix_classifications_award_year ON classifications(award_code, published_year);
GO

-- Pay rates table
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='pay_rates' AND xtype='U')
CREATE TABLE pay_rates (
    id INT IDENTITY(1,1) PRIMARY KEY,
    classification_fixed_id INT NOT NULL,
    award_code NVARCHAR(50) NOT NULL,
    base_pay_rate_id NVARCHAR(50) NULL,
    base_rate_type NVARCHAR(50) NULL,
    base_rate DECIMAL(18,4) NULL,
    calculated_pay_rate_id NVARCHAR(50) NULL,
    calculated_rate_type NVARCHAR(50) NULL,
    calculated_rate DECIMAL(18,4) NULL,
    parent_classification_name NVARCHAR(500) NULL,
    classification NVARCHAR(500) NULL,
    classification_level INT NULL,
    employee_rate_type_code NVARCHAR(20) NULL,
    operative_from DATETIME2 NULL,
    operative_to DATETIME2 NULL,
    version_number INT NULL,
    last_modified_datetime DATETIME2 NULL,
    published_year INT NULL,
    created_at DATETIME2 DEFAULT GETUTCDATE(),
    updated_at DATETIME2 DEFAULT GETUTCDATE()
);
GO

CREATE INDEX IF NOT EXISTS ix_pay_rates_award ON pay_rates(award_code);
GO

CREATE INDEX IF NOT EXISTS ix_pay_rates_award_year ON pay_rates(award_code, published_year);
GO

-- Expense allowances table
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='expense_allowances' AND xtype='U')
CREATE TABLE expense_allowances (
    id INT IDENTITY(1,1) PRIMARY KEY,
    expense_allowance_fixed_id INT NOT NULL,
    award_code NVARCHAR(50) NOT NULL,
    clause_fixed_id INT NULL,
    clauses NVARCHAR(200) NULL,
    parent_allowance NVARCHAR(500) NULL,
    allowance NVARCHAR(500) NULL,
    is_all_purpose BIT NULL,
    allowance_amount DECIMAL(18,4) NULL,
    payment_frequency NVARCHAR(50) NULL,
    last_adjusted_year INT NULL,
    cpi_quarter_last_adjusted NVARCHAR(50) NULL,
    operative_from DATETIME2 NULL,
    operative_to DATETIME2 NULL,
    version_number INT NULL,
    last_modified_datetime DATETIME2 NULL,
    published_year INT NULL,
    created_at DATETIME2 DEFAULT GETUTCDATE(),
    updated_at DATETIME2 DEFAULT GETUTCDATE()
);
GO

CREATE INDEX IF NOT EXISTS ix_expense_allowances_award ON expense_allowances(award_code);
GO

CREATE INDEX IF NOT EXISTS ix_expense_allowances_award_year ON expense_allowances(award_code, published_year);
GO

-- Wage allowances table
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='wage_allowances' AND xtype='U')
CREATE TABLE wage_allowances (
    id INT IDENTITY(1,1) PRIMARY KEY,
    wage_allowance_fixed_id INT NOT NULL,
    award_code NVARCHAR(50) NOT NULL,
    clause_fixed_id INT NULL,
    clauses NVARCHAR(200) NULL,
    parent_allowance NVARCHAR(500) NULL,
    allowance NVARCHAR(500) NULL,
    is_all_purpose BIT NULL,
    rate DECIMAL(18,4) NULL,
    rate_unit NVARCHAR(50) NULL,
    base_pay_rate_id NVARCHAR(50) NULL,
    allowance_amount DECIMAL(18,4) NULL,
    payment_frequency NVARCHAR(50) NULL,
    operative_from DATETIME2 NULL,
    operative_to DATETIME2 NULL,
    version_number INT NULL,
    last_modified_datetime DATETIME2 NULL,
    published_year INT NULL,
    created_at DATETIME2 DEFAULT GETUTCDATE(),
    updated_at DATETIME2 DEFAULT GETUTCDATE()
);
GO

CREATE INDEX IF NOT EXISTS ix_wage_allowances_award ON wage_allowances(award_code);
GO

CREATE INDEX IF NOT EXISTS ix_wage_allowances_award_year ON wage_allowances(award_code, published_year);
GO

PRINT 'Base tables created successfully';
GO
