-- Migration: 001_create_tbl_awards_detailed_and_stored_procedures.sql
-- Creates TblAwardsDetailed table and stored procedures for Rule Engine
-- Run against MS SQL Server

-- Create TblAwardsDetailed table (normalized from staging tables)
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
    record_type NVARCHAR(50) NULL, -- Classification, PayRate, ExpenseAllowance, WageAllowance
    is_active BIT DEFAULT 1,
    compiled_at DATETIME2 DEFAULT GETUTCDATE(),
    created_at DATETIME2 DEFAULT GETUTCDATE(),
    updated_at DATETIME2 DEFAULT GETUTCDATE()
);
GO

-- Create indexes for better query performance
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name='ix_tbl_awards_detailed_award_code' AND object_id = OBJECT_ID('TblAwardsDetailed'))
CREATE INDEX ix_tbl_awards_detailed_award_code ON TblAwardsDetailed(award_code);
GO

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name='ix_tbl_awards_detailed_record_type' AND object_id = OBJECT_ID('TblAwardsDetailed'))
CREATE INDEX ix_tbl_awards_detailed_record_type ON TblAwardsDetailed(record_type);
GO

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name='ix_tbl_awards_detailed_award_code_record_type' AND object_id = OBJECT_ID('TblAwardsDetailed'))
CREATE INDEX ix_tbl_awards_detailed_award_code_record_type ON TblAwardsDetailed(award_code, record_type);
GO

-- Drop existing stored procedures if they exist
IF EXISTS (SELECT * FROM sys.objects WHERE type = 'P' AND name = 'sp_CompileAwardsDetailed')
DROP PROCEDURE sp_CompileAwardsDetailed;
GO

-- Stored Procedure: sp_CompileAwardsDetailed
-- Purpose: Populate TblAwardsDetailed from staging tables with all award combinations
-- This procedure creates a comprehensive denormalized view of award data
CREATE PROCEDURE sp_CompileAwardsDetailed
    @award_code NVARCHAR(50) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    BEGIN TRY
        -- Start transaction
        BEGIN TRANSACTION;
        
        -- Clear existing data for the award(s) if @award_code is specified
        IF @award_code IS NOT NULL
        BEGIN
            DELETE FROM TblAwardsDetailed 
            WHERE award_code = @award_code;
        END
        ELSE
        BEGIN
            -- If no award specified, clear all and rebuild from scratch
            DELETE FROM TblAwardsDetailed;
        END
        
        -- Insert records for Classifications
        INSERT INTO TblAwardsDetailed (
            award_code, award_name, award_id, award_fixed_id, award_operative_from, award_operative_to,
            version_number, published_year, classification_fixed_id, classification_name, 
            parent_classification_name, classification_level, classification_clauses, 
            classification_clause_description, record_type, compiled_at
        )
        SELECT 
            a.code, a.name, a.award_id, a.award_fixed_id, a.award_operative_from, a.award_operative_to,
            a.version_number, a.published_year, c.classification_fixed_id, c.classification,
            c.parent_classification_name, c.classification_level, c.clauses, c.clause_description,
            'Classification', GETUTCDATE()
        FROM Stg_TblAwards a
        INNER JOIN Stg_TblClassifications c ON a.code = c.award_code
        WHERE (@award_code IS NULL OR a.code = @award_code);
        
        -- Insert records for Pay Rates
        INSERT INTO TblAwardsDetailed (
            award_code, award_name, award_id, award_fixed_id, award_operative_from, award_operative_to,
            version_number, published_year, classification_fixed_id, classification_name,
            parent_classification_name, classification_level, base_pay_rate_id, base_rate_type,
            base_rate, calculated_pay_rate_id, calculated_rate_type, calculated_rate,
            employee_rate_type_code, record_type, compiled_at
        )
        SELECT 
            a.code, a.name, a.award_id, a.award_fixed_id, a.award_operative_from, a.award_operative_to,
            a.version_number, a.published_year, p.classification_fixed_id, p.classification,
            p.parent_classification_name, p.classification_level, p.base_pay_rate_id, p.base_rate_type,
            p.base_rate, p.calculated_pay_rate_id, p.calculated_rate_type, p.calculated_rate,
            p.employee_rate_type_code, 'PayRate', GETUTCDATE()
        FROM Stg_TblAwards a
        INNER JOIN Stg_TblPayRates p ON a.code = p.award_code
        WHERE (@award_code IS NULL OR a.code = @award_code);
        
        -- Insert records for Expense Allowances
        INSERT INTO TblAwardsDetailed (
            award_code, award_name, award_id, award_fixed_id, award_operative_from, award_operative_to,
            version_number, published_year, expense_allowance_fixed_id, expense_clause_fixed_id,
            expense_clauses, expense_allowance_name, parent_expense_allowance, expense_allowance_amount,
            expense_payment_frequency, expense_is_all_purpose, expense_last_adjusted_year, 
            expense_cpi_quarter, record_type, compiled_at
        )
        SELECT 
            a.code, a.name, a.award_id, a.award_fixed_id, a.award_operative_from, a.award_operative_to,
            a.version_number, a.published_year, e.expense_allowance_fixed_id, e.clause_fixed_id,
            e.clauses, e.allowance, e.parent_allowance, e.allowance_amount,
            e.payment_frequency, e.is_all_purpose, e.last_adjusted_year, e.cpi_quarter_last_adjusted,
            'ExpenseAllowance', GETUTCDATE()
        FROM Stg_TblAwards a
        INNER JOIN Stg_TblExpenseAllowances e ON a.code = e.award_code
        WHERE (@award_code IS NULL OR a.code = @award_code);
        
        -- Insert records for Wage Allowances
        INSERT INTO TblAwardsDetailed (
            award_code, award_name, award_id, award_fixed_id, award_operative_from, award_operative_to,
            version_number, published_year, wage_allowance_fixed_id, wage_clause_fixed_id,
            wage_clauses, wage_allowance_name, parent_wage_allowance, wage_allowance_rate,
            wage_allowance_rate_unit, wage_allowance_amount, wage_payment_frequency, 
            wage_is_all_purpose, record_type, compiled_at
        )
        SELECT 
            a.code, a.name, a.award_id, a.award_fixed_id, a.award_operative_from, a.award_operative_to,
            a.version_number, a.published_year, w.wage_allowance_fixed_id, w.clause_fixed_id,
            w.clauses, w.allowance, w.parent_allowance, w.rate,
            w.rate_unit, w.allowance_amount, w.payment_frequency, w.is_all_purpose,
            'WageAllowance', GETUTCDATE()
        FROM Stg_TblAwards a
        INNER JOIN Stg_TblWageAllowances w ON a.code = w.award_code
        WHERE (@award_code IS NULL OR a.code = @award_code);
        
        -- Commit transaction
        COMMIT TRANSACTION;
        
        -- Return success status
        SELECT 'Success' as Status, @@ROWCOUNT as TotalRecordsCompiled;
        
    END TRY
    BEGIN CATCH
        -- Rollback on error
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;
        
        -- Return error status
        SELECT 'Error' as Status, ERROR_MESSAGE() as ErrorMessage;
    END CATCH
END
GO

-- Stored Procedure: sp_GetAwardsDetailed
-- Purpose: Retrieve detailed award information with optional filtering
CREATE PROCEDURE sp_GetAwardsDetailed
    @award_code NVARCHAR(50) = NULL,
    @record_type NVARCHAR(50) = NULL,
    @classification_fixed_id INT = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    SELECT 
        id, award_code, award_name, award_id, award_fixed_id, award_operative_from, award_operative_to,
        version_number, published_year, classification_fixed_id, classification_name,
        parent_classification_name, classification_level, classification_clauses, 
        classification_clause_description, base_pay_rate_id, base_rate_type, base_rate,
        calculated_pay_rate_id, calculated_rate_type, calculated_rate, employee_rate_type_code,
        expense_allowance_fixed_id, expense_clause_fixed_id, expense_clauses, expense_allowance_name,
        parent_expense_allowance, expense_allowance_amount, expense_payment_frequency, expense_is_all_purpose,
        expense_last_adjusted_year, expense_cpi_quarter, wage_allowance_fixed_id, wage_clause_fixed_id,
        wage_clauses, wage_allowance_name, parent_wage_allowance, wage_allowance_rate, wage_allowance_rate_unit,
        wage_allowance_amount, wage_payment_frequency, wage_is_all_purpose, record_type, is_active,
        compiled_at, created_at, updated_at
    FROM TblAwardsDetailed
    WHERE 
        (@award_code IS NULL OR award_code = @award_code)
        AND (@record_type IS NULL OR record_type = @record_type)
        AND (@classification_fixed_id IS NULL OR classification_fixed_id = @classification_fixed_id)
    ORDER BY award_code, record_type, id;
END
GO
