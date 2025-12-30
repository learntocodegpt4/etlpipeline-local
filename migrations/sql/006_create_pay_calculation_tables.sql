-- Migration: 006_create_pay_calculation_tables.sql
-- Creates tables for penalty rates, conditions, and calculated pay rates
-- These tables support comprehensive pay calculation scenarios
-- Run against MS SQL Server

-- =============================================
-- Penalty Rates Reference Table
-- Stores FWC-defined penalty multipliers and rates
-- =============================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='TblPenaltyRates' AND xtype='U')
CREATE TABLE TblPenaltyRates (
    id INT IDENTITY(1,1) PRIMARY KEY,
    award_code NVARCHAR(50) NOT NULL,
    penalty_type NVARCHAR(50) NOT NULL, -- SATURDAY, SUNDAY, PUBLIC_HOLIDAY, NIGHT_SHIFT, AFTERNOON_SHIFT, EARLY_MORNING, OVERTIME_FIRST2HR, OVERTIME_AFTER2HR
    penalty_category NVARCHAR(50) NULL, -- TIME_BASED, SHIFT_BASED, OVERTIME
    penalty_multiplier DECIMAL(5,4) NULL, -- e.g., 1.5000 for 150%, 2.0000 for 200%
    penalty_flat_amount DECIMAL(10,2) NULL, -- For flat rate penalties
    penalty_calculation_method NVARCHAR(20) NOT NULL DEFAULT 'MULTIPLIER', -- MULTIPLIER, FLAT, ADDITIVE, HIGHER
    
    -- Time conditions
    applies_from_time TIME NULL, -- e.g., '19:00:00' for 7 PM
    applies_to_time TIME NULL, -- e.g., '07:00:00' for 7 AM next day
    applies_from_day NVARCHAR(20) NULL, -- MONDAY, TUESDAY, etc.
    applies_to_day NVARCHAR(20) NULL,
    
    -- Employment type filters
    applies_to_employment_type NVARCHAR(50) NULL, -- FULL_TIME, PART_TIME, CASUAL, ALL
    
    -- Effective dates
    effective_from DATE NOT NULL,
    effective_to DATE NULL,
    
    -- FWC clause reference
    clause_reference NVARCHAR(200) NULL,
    clause_description NVARCHAR(1000) NULL,
    
    -- Metadata
    is_active BIT NOT NULL DEFAULT 1,
    created_at DATETIME2 DEFAULT GETUTCDATE(),
    updated_at DATETIME2 DEFAULT GETUTCDATE()
);
GO

IF NOT EXISTS (
        SELECT 1 FROM sys.indexes 
        WHERE name = 'ix_tblpenaltyrates_award' 
            AND object_id = OBJECT_ID('dbo.TblPenaltyRates')
)
CREATE INDEX ix_tblpenaltyrates_award ON TblPenaltyRates(award_code);
GO

IF NOT EXISTS (
        SELECT 1 FROM sys.indexes 
        WHERE name = 'ix_tblpenaltyrates_award_type' 
            AND object_id = OBJECT_ID('dbo.TblPenaltyRates')
)
CREATE INDEX ix_tblpenaltyrates_award_type ON TblPenaltyRates(award_code, penalty_type);
GO

IF NOT EXISTS (
        SELECT 1 FROM sys.indexes 
        WHERE name = 'ix_tblpenaltyrates_active' 
            AND object_id = OBJECT_ID('dbo.TblPenaltyRates')
)
CREATE INDEX ix_tblpenaltyrates_active ON TblPenaltyRates(is_active, effective_from, effective_to);
GO

-- =============================================
-- Junior Rates Reference Table
-- Stores age-based pay rate percentages
-- =============================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='TblJuniorRates' AND xtype='U')
CREATE TABLE TblJuniorRates (
    id INT IDENTITY(1,1) PRIMARY KEY,
    award_code NVARCHAR(50) NOT NULL,
    age_from INT NOT NULL, -- e.g., 16
    age_to INT NOT NULL, -- e.g., 16 (same year) or 17
    junior_percentage DECIMAL(5,4) NOT NULL, -- e.g., 0.5500 for 55%, 0.7000 for 70%
    
    -- Effective dates
    effective_from DATE NOT NULL,
    effective_to DATE NULL,
    
    -- FWC clause reference
    clause_reference NVARCHAR(200) NULL,
    clause_description NVARCHAR(1000) NULL,
    
    -- Metadata
    is_active BIT NOT NULL DEFAULT 1,
    created_at DATETIME2 DEFAULT GETUTCDATE(),
    updated_at DATETIME2 DEFAULT GETUTCDATE()
);
GO

IF NOT EXISTS (
        SELECT 1 FROM sys.indexes 
        WHERE name = 'ix_tbljuniorrates_award' 
            AND object_id = OBJECT_ID('dbo.TblJuniorRates')
)
CREATE INDEX ix_tbljuniorrates_award ON TblJuniorRates(award_code);
GO

IF NOT EXISTS (
        SELECT 1 FROM sys.indexes 
        WHERE name = 'ix_tbljuniorrates_age' 
            AND object_id = OBJECT_ID('dbo.TblJuniorRates')
)
CREATE INDEX ix_tbljuniorrates_age ON TblJuniorRates(age_from, age_to);
GO

-- =============================================
-- Casual Loading Reference Table
-- Stores casual employment loading percentages
-- =============================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='TblCasualLoadings' AND xtype='U')
CREATE TABLE TblCasualLoadings (
    id INT IDENTITY(1,1) PRIMARY KEY,
    award_code NVARCHAR(50) NOT NULL,
    casual_loading_percentage DECIMAL(5,4) NOT NULL, -- e.g., 0.2500 for 25%
    
    -- Optional classification-specific loadings
    classification_fixed_id INT NULL,
    classification_name NVARCHAR(500) NULL,
    
    -- Effective dates
    effective_from DATE NOT NULL,
    effective_to DATE NULL,
    
    -- FWC clause reference
    clause_reference NVARCHAR(200) NULL,
    clause_description NVARCHAR(1000) NULL,
    
    -- Metadata
    is_active BIT NOT NULL DEFAULT 1,
    created_at DATETIME2 DEFAULT GETUTCDATE(),
    updated_at DATETIME2 DEFAULT GETUTCDATE()
);
GO

IF NOT EXISTS (
        SELECT 1 FROM sys.indexes 
        WHERE name = 'ix_tblcasualloadings_award' 
            AND object_id = OBJECT_ID('dbo.TblCasualLoadings')
)
CREATE INDEX ix_tblcasualloadings_award ON TblCasualLoadings(award_code);
GO

-- =============================================
-- Allowance Conditions Table
-- Stores conditional allowances (meal, uniform, tools, etc.)
-- =============================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='TblAllowanceConditions' AND xtype='U')
CREATE TABLE TblAllowanceConditions (
    id INT IDENTITY(1,1) PRIMARY KEY,
    award_code NVARCHAR(50) NOT NULL,
    allowance_type NVARCHAR(50) NOT NULL, -- MEAL, UNIFORM, LAUNDRY, TOOLS, SPLIT_SHIFT, ONCALL, etc.
    allowance_name NVARCHAR(500) NOT NULL,
    allowance_amount DECIMAL(10,2) NOT NULL,
    allowance_frequency NVARCHAR(50) NOT NULL, -- PER_SHIFT, PER_DAY, PER_WEEK, PER_OCCURRENCE
    
    -- Condition logic
    condition_type NVARCHAR(50) NULL, -- TIME_BASED, DURATION_BASED, SHIFT_TYPE, ALWAYS
    condition_operator NVARCHAR(20) NULL, -- GREATER_THAN, LESS_THAN, EQUALS, BETWEEN, AFTER, BEFORE
    condition_value NVARCHAR(100) NULL, -- e.g., '21:00' for time, '8' for hours
    condition_value2 NVARCHAR(100) NULL, -- For BETWEEN operator
    
    -- Effective dates
    effective_from DATE NOT NULL,
    effective_to DATE NULL,
    
    -- FWC clause reference
    clause_reference NVARCHAR(200) NULL,
    clause_description NVARCHAR(1000) NULL,
    
    -- Metadata
    is_active BIT NOT NULL DEFAULT 1,
    created_at DATETIME2 DEFAULT GETUTCDATE(),
    updated_at DATETIME2 DEFAULT GETUTCDATE()
);
GO

IF NOT EXISTS (
        SELECT 1 FROM sys.indexes 
        WHERE name = 'ix_tblallowanceconditions_award' 
            AND object_id = OBJECT_ID('dbo.TblAllowanceConditions')
)
CREATE INDEX ix_tblallowanceconditions_award ON TblAllowanceConditions(award_code);
GO

IF NOT EXISTS (
        SELECT 1 FROM sys.indexes 
        WHERE name = 'ix_tblallowanceconditions_type' 
            AND object_id = OBJECT_ID('dbo.TblAllowanceConditions')
)
CREATE INDEX ix_tblallowanceconditions_type ON TblAllowanceConditions(allowance_type);
GO

-- =============================================
-- Apprentice/Trainee Rates Table
-- Stores progression rates for apprentices and trainees
-- =============================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='TblApprenticeRates' AND xtype='U')
CREATE TABLE TblApprenticeRates (
    id INT IDENTITY(1,1) PRIMARY KEY,
    award_code NVARCHAR(50) NOT NULL,
    apprentice_type NVARCHAR(50) NOT NULL, -- APPRENTICE, TRAINEE
    year_or_level INT NOT NULL, -- 1, 2, 3, 4
    rate_percentage DECIMAL(5,4) NOT NULL, -- e.g., 0.5500 for 55% of qualified rate
    
    -- Optional qualification details
    qualification_level NVARCHAR(200) NULL, -- e.g., 'Certificate III'
    
    -- Effective dates
    effective_from DATE NOT NULL,
    effective_to DATE NULL,
    
    -- FWC clause reference
    clause_reference NVARCHAR(200) NULL,
    clause_description NVARCHAR(1000) NULL,
    
    -- Metadata
    is_active BIT NOT NULL DEFAULT 1,
    created_at DATETIME2 DEFAULT GETUTCDATE(),
    updated_at DATETIME2 DEFAULT GETUTCDATE()
);
GO

IF NOT EXISTS (
        SELECT 1 FROM sys.indexes 
        WHERE name = 'ix_tblapprenticerates_award' 
            AND object_id = OBJECT_ID('dbo.TblApprenticeRates')
)
CREATE INDEX ix_tblapprenticerates_award ON TblApprenticeRates(award_code);
GO

IF NOT EXISTS (
        SELECT 1 FROM sys.indexes 
        WHERE name = 'ix_tblapprenticerates_type_year' 
            AND object_id = OBJECT_ID('dbo.TblApprenticeRates')
)
CREATE INDEX ix_tblapprenticerates_type_year ON TblApprenticeRates(apprentice_type, year_or_level);
GO

-- =============================================
-- Calculated Pay Rates Table
-- Stores ALL possible pay rate combinations
-- This is the master table for UI display and pay calculations
-- =============================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='TblCalculatedPayRates' AND xtype='U')
CREATE TABLE TblCalculatedPayRates (
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    
    -- Award and classification linkage
    award_code NVARCHAR(50) NOT NULL,
    award_name NVARCHAR(500) NULL,
    classification_fixed_id INT NULL,
    classification_name NVARCHAR(500) NULL,
    classification_level INT NULL,
    
    -- Base rate information
    base_pay_rate_id NVARCHAR(50) NULL,
    base_rate DECIMAL(18,4) NOT NULL,
    base_rate_type NVARCHAR(50) NULL, -- HOURLY, WEEKLY, ANNUAL
    
    -- Employee attributes
    employment_type NVARCHAR(50) NOT NULL, -- FULL_TIME, PART_TIME, CASUAL
    employee_age_category NVARCHAR(50) NOT NULL, -- ADULT, AGE_20, AGE_19, AGE_18, AGE_17, AGE_16, UNDER_16
    employee_category NVARCHAR(50) NULL, -- STANDARD, APPRENTICE_YEAR1, APPRENTICE_YEAR2, TRAINEE, etc.
    
    -- Scenario details
    day_type NVARCHAR(50) NOT NULL, -- WEEKDAY, SATURDAY, SUNDAY, PUBLIC_HOLIDAY
    shift_type NVARCHAR(50) NOT NULL, -- STANDARD, NIGHT, AFTERNOON, EARLY_MORNING, OVERTIME_FIRST2HR, OVERTIME_AFTER2HR
    time_range NVARCHAR(100) NULL, -- e.g., '19:00-23:00' for context
    
    -- Calculation breakdown
    casual_loading_applied DECIMAL(5,4) NULL, -- e.g., 0.2500 for 25%
    casual_loaded_rate DECIMAL(18,4) NULL,
    
    junior_percentage_applied DECIMAL(5,4) NULL, -- e.g., 0.7000 for 70%
    junior_adjusted_rate DECIMAL(18,4) NULL,
    
    apprentice_percentage_applied DECIMAL(5,4) NULL,
    apprentice_adjusted_rate DECIMAL(18,4) NULL,
    
    penalty_type NVARCHAR(50) NULL,
    penalty_multiplier_applied DECIMAL(5,4) NULL, -- e.g., 1.5000 for 150%
    penalty_flat_amount_applied DECIMAL(10,2) NULL,
    
    -- Final calculated rate
    calculated_hourly_rate DECIMAL(18,4) NOT NULL,
    calculated_rate_description NVARCHAR(1000) NULL, -- Human-readable description
    
    -- Calculation formula for audit
    calculation_steps NVARCHAR(2000) NULL, -- e.g., "Base $25.00 × Casual 1.25 = $31.25 × Sunday 2.0 = $62.50"
    
    -- Applicable allowances (comma-separated IDs or JSON)
    applicable_allowance_ids NVARCHAR(500) NULL,
    applicable_allowance_total DECIMAL(10,2) NULL,
    
    -- Effective dates
    effective_from DATE NOT NULL,
    effective_to DATE NULL,
    
    -- FWC clause references
    penalty_clause_reference NVARCHAR(200) NULL,
    casual_clause_reference NVARCHAR(200) NULL,
    junior_clause_reference NVARCHAR(200) NULL,
    
    -- Metadata
    is_active BIT NOT NULL DEFAULT 1,
    compiled_at DATETIME2 DEFAULT GETUTCDATE(),
    compiled_by NVARCHAR(100) DEFAULT 'SYSTEM',
    created_at DATETIME2 DEFAULT GETUTCDATE(),
    updated_at DATETIME2 DEFAULT GETUTCDATE()
);
GO

IF NOT EXISTS (
        SELECT 1 FROM sys.indexes 
        WHERE name = 'ix_tblcalculatedpayrates_award' 
            AND object_id = OBJECT_ID('dbo.TblCalculatedPayRates')
)
CREATE INDEX ix_tblcalculatedpayrates_award ON TblCalculatedPayRates(award_code);
GO

IF NOT EXISTS (
        SELECT 1 FROM sys.indexes 
        WHERE name = 'ix_tblcalculatedpayrates_award_class' 
            AND object_id = OBJECT_ID('dbo.TblCalculatedPayRates')
)
CREATE INDEX ix_tblcalculatedpayrates_award_class ON TblCalculatedPayRates(award_code, classification_fixed_id);
GO

IF NOT EXISTS (
        SELECT 1 FROM sys.indexes 
        WHERE name = 'ix_tblcalculatedpayrates_scenario' 
            AND object_id = OBJECT_ID('dbo.TblCalculatedPayRates')
)
CREATE INDEX ix_tblcalculatedpayrates_scenario ON TblCalculatedPayRates(employment_type, day_type, shift_type);
GO

IF NOT EXISTS (
        SELECT 1 FROM sys.indexes 
        WHERE name = 'ix_tblcalculatedpayrates_age' 
            AND object_id = OBJECT_ID('dbo.TblCalculatedPayRates')
)
CREATE INDEX ix_tblcalculatedpayrates_age ON TblCalculatedPayRates(employee_age_category);
GO

IF NOT EXISTS (
        SELECT 1 FROM sys.indexes 
        WHERE name = 'ix_tblcalculatedpayrates_active' 
            AND object_id = OBJECT_ID('dbo.TblCalculatedPayRates')
)
CREATE INDEX ix_tblcalculatedpayrates_active ON TblCalculatedPayRates(is_active, effective_from, effective_to);
GO

IF NOT EXISTS (
        SELECT 1 FROM sys.indexes 
        WHERE name = 'ix_tblcalculatedpayrates_rate' 
            AND object_id = OBJECT_ID('dbo.TblCalculatedPayRates')
)
CREATE INDEX ix_tblcalculatedpayrates_rate ON TblCalculatedPayRates(calculated_hourly_rate);
GO

-- =============================================
-- Calculation Log Table
-- Tracks when pay rate calculations were performed
-- =============================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='TblPayCalculationLog' AND xtype='U')
CREATE TABLE TblPayCalculationLog (
    id INT IDENTITY(1,1) PRIMARY KEY,
    award_code NVARCHAR(50) NULL,
    calculation_type NVARCHAR(50) NOT NULL, -- ALL_AWARDS, SINGLE_AWARD, SINGLE_CLASSIFICATION
    total_records_created INT NOT NULL,
    calculation_started_at DATETIME2 NOT NULL,
    calculation_completed_at DATETIME2 NOT NULL,
    calculation_duration_seconds INT NULL,
    status NVARCHAR(20) NOT NULL, -- SUCCESS, FAILED, PARTIAL
    error_message NVARCHAR(2000) NULL,
    executed_by NVARCHAR(100) NOT NULL,
    created_at DATETIME2 DEFAULT GETUTCDATE()
);
GO

IF NOT EXISTS (
        SELECT 1 FROM sys.indexes 
        WHERE name = 'ix_tblpaycalculationlog_award' 
            AND object_id = OBJECT_ID('dbo.TblPayCalculationLog')
)
CREATE INDEX ix_tblpaycalculationlog_award ON TblPayCalculationLog(award_code);
GO

IF NOT EXISTS (
        SELECT 1 FROM sys.indexes 
        WHERE name = 'ix_tblpaycalculationlog_date' 
            AND object_id = OBJECT_ID('dbo.TblPayCalculationLog')
)
CREATE INDEX ix_tblpaycalculationlog_date ON TblPayCalculationLog(calculation_started_at);
GO

-- =============================================
-- Sample Data for Testing
-- Insert common penalty rates (examples based on typical FWC awards)
-- =============================================

-- Weekend penalties (Saturday)
INSERT INTO TblPenaltyRates (award_code, penalty_type, penalty_category, penalty_multiplier, penalty_calculation_method, effective_from, clause_reference)
VALUES 
('SAMPLE001', 'SATURDAY', 'TIME_BASED', 1.5000, 'MULTIPLIER', '2024-01-01', 'Clause 15.3 - Saturday work'),
('SAMPLE001', 'SATURDAY_AFTER_7PM', 'TIME_BASED', 1.7500, 'MULTIPLIER', '2024-01-01', 'Clause 15.3(b) - Saturday after 7 PM');

-- Weekend penalties (Sunday)
INSERT INTO TblPenaltyRates (award_code, penalty_type, penalty_category, penalty_multiplier, penalty_calculation_method, effective_from, clause_reference)
VALUES 
('SAMPLE001', 'SUNDAY', 'TIME_BASED', 2.0000, 'MULTIPLIER', '2024-01-01', 'Clause 15.4 - Sunday work');

-- Public holiday
INSERT INTO TblPenaltyRates (award_code, penalty_type, penalty_category, penalty_multiplier, penalty_calculation_method, effective_from, clause_reference)
VALUES 
('SAMPLE001', 'PUBLIC_HOLIDAY', 'TIME_BASED', 2.5000, 'MULTIPLIER', '2024-01-01', 'Clause 15.5 - Public holiday work');

-- Night shift
INSERT INTO TblPenaltyRates (award_code, penalty_type, penalty_category, penalty_multiplier, penalty_calculation_method, applies_from_time, applies_to_time, effective_from, clause_reference)
VALUES 
('SAMPLE001', 'NIGHT_SHIFT', 'SHIFT_BASED', 1.1500, 'MULTIPLIER', '22:00', '07:00', '2024-01-01', 'Clause 16.2 - Night shift 10pm-7am');

-- Overtime
INSERT INTO TblPenaltyRates (award_code, penalty_type, penalty_category, penalty_multiplier, penalty_calculation_method, effective_from, clause_reference)
VALUES 
('SAMPLE001', 'OVERTIME_FIRST2HR', 'OVERTIME', 1.5000, 'MULTIPLIER', '2024-01-01', 'Clause 17.1 - Overtime first 2 hours'),
('SAMPLE001', 'OVERTIME_AFTER2HR', 'OVERTIME', 2.0000, 'MULTIPLIER', '2024-01-01', 'Clause 17.2 - Overtime after 2 hours');

-- Junior rates
INSERT INTO TblJuniorRates (award_code, age_from, age_to, junior_percentage, effective_from, clause_reference)
VALUES 
('SAMPLE001', 16, 16, 0.5000, '2024-01-01', 'Clause 12.1 - Junior rates'),
('SAMPLE001', 17, 17, 0.6000, '2024-01-01', 'Clause 12.1 - Junior rates'),
('SAMPLE001', 18, 18, 0.7000, '2024-01-01', 'Clause 12.1 - Junior rates'),
('SAMPLE001', 19, 19, 0.8500, '2024-01-01', 'Clause 12.1 - Junior rates'),
('SAMPLE001', 20, 20, 0.9500, '2024-01-01', 'Clause 12.1 - Junior rates');

-- Casual loading
INSERT INTO TblCasualLoadings (award_code, casual_loading_percentage, effective_from, clause_reference)
VALUES 
('SAMPLE001', 0.2500, '2024-01-01', 'Clause 11.5 - Casual loading 25%');

-- Allowances
INSERT INTO TblAllowanceConditions (award_code, allowance_type, allowance_name, allowance_amount, allowance_frequency, condition_type, condition_operator, condition_value, effective_from, clause_reference)
VALUES 
('SAMPLE001', 'MEAL', 'Meal allowance - late finish', 15.00, 'PER_OCCURRENCE', 'TIME_BASED', 'AFTER', '21:00', '2024-01-01', 'Clause 18.3 - Meal allowance'),
('SAMPLE001', 'LAUNDRY', 'Laundry allowance', 1.50, 'PER_DAY', 'ALWAYS', NULL, NULL, '2024-01-01', 'Clause 19.2 - Laundry allowance'),
('SAMPLE001', 'SPLIT_SHIFT', 'Split shift allowance', 8.50, 'PER_OCCURRENCE', 'SHIFT_TYPE', 'EQUALS', 'SPLIT', '2024-01-01', 'Clause 16.5 - Split shift');

-- Apprentice rates
INSERT INTO TblApprenticeRates (award_code, apprentice_type, year_or_level, rate_percentage, effective_from, clause_reference)
VALUES 
('SAMPLE001', 'APPRENTICE', 1, 0.5500, '2024-01-01', 'Clause 13.2 - Apprentice rates'),
('SAMPLE001', 'APPRENTICE', 2, 0.6500, '2024-01-01', 'Clause 13.2 - Apprentice rates'),
('SAMPLE001', 'APPRENTICE', 3, 0.8000, '2024-01-01', 'Clause 13.2 - Apprentice rates'),
('SAMPLE001', 'APPRENTICE', 4, 0.9500, '2024-01-01', 'Clause 13.2 - Apprentice rates');

GO

PRINT 'Pay calculation tables created successfully';
PRINT 'Sample reference data inserted';
PRINT 'Ready for stored procedure implementation';
GO
