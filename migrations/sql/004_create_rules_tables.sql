-- Migration: 004_create_rules_tables.sql
-- Creates tables for rules engine and awards compilation

-- Awards Summary table - stores compiled awards summaries
-- Recreate table for modifications
IF OBJECT_ID('TblAwardsSummary', 'U') IS NOT NULL
    DROP TABLE TblAwardsSummary;
GO

CREATE TABLE TblAwardsSummary (
    id INT IDENTITY(1,1) PRIMARY KEY,
    award_code NVARCHAR(50) NOT NULL,
    award_name NVARCHAR(500) NULL,
    industry_type NVARCHAR(100) NULL,
    total_classifications INT DEFAULT 0,
    total_pay_rates INT DEFAULT 0,
    total_expense_allowances INT DEFAULT 0,
    total_wage_allowances INT DEFAULT 0,
    min_base_rate DECIMAL(18,4) NULL,
    max_base_rate DECIMAL(18,4) NULL,
    avg_base_rate DECIMAL(18,4) NULL,
    is_custom BIT DEFAULT 0,
    is_active BIT DEFAULT 1,
    compiled_at DATETIME2 DEFAULT GETUTCDATE(),
    created_at DATETIME2 DEFAULT GETUTCDATE(),
    updated_at DATETIME2 DEFAULT GETUTCDATE()
);
GO

IF EXISTS (SELECT * FROM sys.indexes WHERE name='ix_tblawardssummary_code' AND object_id = OBJECT_ID('TblAwardsSummary'))
    DROP INDEX ix_tblawardssummary_code ON TblAwardsSummary;
GO
CREATE INDEX ix_tblawardssummary_code ON TblAwardsSummary(award_code);
GO

IF EXISTS (SELECT * FROM sys.indexes WHERE name='ix_tblawardssummary_industry' AND object_id = OBJECT_ID('TblAwardsSummary'))
    DROP INDEX ix_tblawardssummary_industry ON TblAwardsSummary;
GO
CREATE INDEX ix_tblawardssummary_industry ON TblAwardsSummary(industry_type);
GO

-- Rules table - stores all rules (simple and complex)
-- Safe drop: ensure dependent FKs are removed first
IF OBJECT_ID('TblRules', 'U') IS NOT NULL
BEGIN
    -- Drop FK on TblAwardRules if it exists
    IF EXISTS (
        SELECT 1 FROM sys.foreign_keys WHERE name = 'FK_award_rules_rule_code'
        AND parent_object_id = OBJECT_ID('TblAwardRules')
    )
    BEGIN
        ALTER TABLE TblAwardRules DROP CONSTRAINT FK_award_rules_rule_code;
    END
    DROP TABLE TblRules;
END
GO

CREATE TABLE TblRules (
    id INT IDENTITY(1,1) PRIMARY KEY,
    rule_code NVARCHAR(50) NOT NULL UNIQUE,
    rule_name NVARCHAR(200) NOT NULL,
    rule_type NVARCHAR(50) NOT NULL, -- 'SIMPLE', 'COMPLEX'
    rule_category NVARCHAR(100) NULL, -- 'PAY_RATE', 'ALLOWANCE', 'CLASSIFICATION', 'COMPLIANCE'
    rule_definition NVARCHAR(MAX) NOT NULL,
    rule_expression NVARCHAR(MAX) NULL,
    priority INT DEFAULT 0,
    is_active BIT DEFAULT 1,
    created_by NVARCHAR(100) DEFAULT 'SYSTEM',
    created_at DATETIME2 DEFAULT GETUTCDATE(),
    updated_at DATETIME2 DEFAULT GETUTCDATE()
);
GO

IF EXISTS (SELECT * FROM sys.indexes WHERE name='ix_tblrules_type' AND object_id = OBJECT_ID('TblRules'))
    DROP INDEX ix_tblrules_type ON TblRules;
GO
CREATE INDEX ix_tblrules_type ON TblRules(rule_type);
GO

IF EXISTS (SELECT * FROM sys.indexes WHERE name='ix_tblrules_category' AND object_id = OBJECT_ID('TblRules'))
    DROP INDEX ix_tblrules_category ON TblRules;
GO
CREATE INDEX ix_tblrules_category ON TblRules(rule_category);
GO

-- Award Rules Mapping - maps rules to awards
-- Drop table cleanly (will be recreated below)
IF OBJECT_ID('TblAwardRules', 'U') IS NOT NULL
    DROP TABLE TblAwardRules;
GO

CREATE TABLE TblAwardRules (
    id INT IDENTITY(1,1) PRIMARY KEY,
    award_code NVARCHAR(50) NOT NULL,
    rule_code NVARCHAR(50) NOT NULL,
    is_applied BIT DEFAULT 0,
    applied_at DATETIME2 NULL,
    result_summary NVARCHAR(MAX) NULL,
    created_at DATETIME2 DEFAULT GETUTCDATE(),
    CONSTRAINT FK_award_rules_rule_code FOREIGN KEY (rule_code) REFERENCES TblRules(rule_code)
);
GO

IF EXISTS (SELECT * FROM sys.indexes WHERE name='ix_tblawardrules_award' AND object_id = OBJECT_ID('TblAwardRules'))
    DROP INDEX ix_tblawardrules_award ON TblAwardRules;
GO
CREATE INDEX ix_tblawardrules_award ON TblAwardRules(award_code);
GO

IF EXISTS (SELECT * FROM sys.indexes WHERE name='ix_tblawardrules_rule' AND object_id = OBJECT_ID('TblAwardRules'))
    DROP INDEX ix_tblawardrules_rule ON TblAwardRules;
GO
CREATE INDEX ix_tblawardrules_rule ON TblAwardRules(rule_code);
GO

-- Custom Awards table - stores custom awards created by system admin
IF OBJECT_ID('TblCustomAwards', 'U') IS NOT NULL
    DROP TABLE TblCustomAwards;
GO

CREATE TABLE TblCustomAwards (
    id INT IDENTITY(1,1) PRIMARY KEY,
    custom_award_code NVARCHAR(50) NOT NULL UNIQUE,
    base_award_code NVARCHAR(50) NOT NULL,
    custom_award_name NVARCHAR(500) NOT NULL,
    tenant_id NVARCHAR(50) NULL,
    organization_id NVARCHAR(50) NULL,
    custom_pay_rate_multiplier DECIMAL(5,2) DEFAULT 1.0,
    min_pay_rate_override DECIMAL(18,4) NULL,
    customizations NVARCHAR(MAX) NULL, -- JSON field for custom settings
    is_active BIT DEFAULT 1,
    created_by NVARCHAR(100) NOT NULL,
    created_at DATETIME2 DEFAULT GETUTCDATE(),
    updated_at DATETIME2 DEFAULT GETUTCDATE()
);
GO

IF EXISTS (SELECT * FROM sys.indexes WHERE name='ix_tblcustomawards_base_code' AND object_id = OBJECT_ID('TblCustomAwards'))
    DROP INDEX ix_tblcustomawards_base_code ON TblCustomAwards;
GO
CREATE INDEX ix_tblcustomawards_base_code ON TblCustomAwards(base_award_code);
GO

IF EXISTS (SELECT * FROM sys.indexes WHERE name='ix_tblcustomawards_tenant' AND object_id = OBJECT_ID('TblCustomAwards'))
    DROP INDEX ix_tblcustomawards_tenant ON TblCustomAwards;
GO
CREATE INDEX ix_tblcustomawards_tenant ON TblCustomAwards(tenant_id);
GO

-- Rule Execution Log - tracks rule execution history
IF OBJECT_ID('TblRuleExecutionLog', 'U') IS NOT NULL
    DROP TABLE TblRuleExecutionLog;
GO

CREATE TABLE TblRuleExecutionLog (
    id INT IDENTITY(1,1) PRIMARY KEY,
    execution_id NVARCHAR(50) NOT NULL,
    rule_code NVARCHAR(50) NOT NULL,
    award_code NVARCHAR(50) NULL,
    execution_status NVARCHAR(20) NOT NULL, -- 'SUCCESS', 'FAILED', 'SKIPPED'
    execution_result NVARCHAR(MAX) NULL,
    error_message NVARCHAR(MAX) NULL,
    execution_duration_ms INT NULL,
    executed_at DATETIME2 DEFAULT GETUTCDATE()
);
GO

IF EXISTS (SELECT * FROM sys.indexes WHERE name='ix_tblruleexecutionlog_exec_id' AND object_id = OBJECT_ID('TblRuleExecutionLog'))
    DROP INDEX ix_tblruleexecutionlog_exec_id ON TblRuleExecutionLog;
GO
CREATE INDEX ix_tblruleexecutionlog_exec_id ON TblRuleExecutionLog(execution_id);
GO

-- Awards Detailed Table - stores comprehensive award information with all related data
-- This table provides maximum information for System Admin UI display
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='TblAwardsDetailed' AND xtype='U')
CREATE TABLE TblAwardsDetailed (
    id INT IDENTITY(1,1) PRIMARY KEY,
    
    -- Award Basic Info
    award_code NVARCHAR(50) NOT NULL,
    award_name NVARCHAR(500) NULL,
    award_id INT NULL,
    award_fixed_id INT NULL,
    award_operative_from DATETIME2 NULL,
    award_operative_to DATETIME2 NULL,
    version_number INT NULL,
    published_year INT NULL,
    
    -- Classification Info
    classification_fixed_id INT NULL,
    classification_name NVARCHAR(500) NULL,
    parent_classification_name NVARCHAR(500) NULL,
    classification_level INT NULL,
    classification_clauses NVARCHAR(200) NULL,
    classification_clause_description NVARCHAR(1000) NULL,
    
    -- Pay Rate Info
    base_pay_rate_id NVARCHAR(50) NULL,
    base_rate_type NVARCHAR(50) NULL,
    base_rate DECIMAL(18,4) NULL,
    calculated_pay_rate_id NVARCHAR(50) NULL,
    calculated_rate_type NVARCHAR(50) NULL,
    calculated_rate DECIMAL(18,4) NULL,
    employee_rate_type_code NVARCHAR(20) NULL,
    
    -- Expense Allowance Info
    expense_allowance_fixed_id INT NULL,
    expense_clause_fixed_id INT NULL,
    expense_clauses NVARCHAR(200) NULL,
    expense_allowance_name NVARCHAR(500) NULL,
    parent_expense_allowance NVARCHAR(500) NULL,
    expense_allowance_amount DECIMAL(18,4) NULL,
    expense_payment_frequency NVARCHAR(50) NULL,
    expense_is_all_purpose BIT NULL,
    expense_last_adjusted_year INT NULL,
    expense_cpi_quarter NVARCHAR(50) NULL,
    
    -- Wage Allowance Info
    wage_allowance_fixed_id INT NULL,
    wage_clause_fixed_id INT NULL,
    wage_clauses NVARCHAR(200) NULL,
    wage_allowance_name NVARCHAR(500) NULL,
    parent_wage_allowance NVARCHAR(500) NULL,
    wage_allowance_rate DECIMAL(18,4) NULL,
    wage_allowance_rate_unit NVARCHAR(50) NULL,
    wage_allowance_amount DECIMAL(18,4) NULL,
    wage_payment_frequency NVARCHAR(50) NULL,
    wage_is_all_purpose BIT NULL,
    
    -- Metadata
    record_type NVARCHAR(50) NOT NULL, -- 'BASE', 'WITH_CLASSIFICATION', 'WITH_PAYRATE', 'WITH_EXPENSE', 'WITH_WAGE'
    is_active BIT DEFAULT 1,
    compiled_at DATETIME2 DEFAULT GETUTCDATE(),
    created_at DATETIME2 DEFAULT GETUTCDATE(),
    updated_at DATETIME2 DEFAULT GETUTCDATE()
);
GO

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name='ix_tblawardsdetailed_award_code' AND object_id = OBJECT_ID('TblAwardsDetailed'))
CREATE INDEX ix_tblawardsdetailed_award_code ON TblAwardsDetailed(award_code);
GO

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name='ix_tblawardsdetailed_record_type' AND object_id = OBJECT_ID('TblAwardsDetailed'))
CREATE INDEX ix_tblawardsdetailed_record_type ON TblAwardsDetailed(record_type);
GO

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name='ix_tblawardsdetailed_classification' AND object_id = OBJECT_ID('TblAwardsDetailed'))
CREATE INDEX ix_tblawardsdetailed_classification ON TblAwardsDetailed(classification_fixed_id);
GO

PRINT 'Rules engine tables created successfully';
GO
