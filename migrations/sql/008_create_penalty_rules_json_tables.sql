-- Migration: 008_create_penalty_rules_json_tables.sql
-- Creates JSON-based penalty rules tables for flexible rule engine
-- Supports complex conditional logic with priority-based execution
-- Run against MS SQL Server

-- =============================================
-- Penalty Rules Table (JSON-based)
-- Stores award-specific penalty rules with JSON conditions
-- =============================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='TblPenaltyRulesJSON' AND xtype='U')
CREATE TABLE TblPenaltyRulesJSON (
    id INT IDENTITY(1,1) PRIMARY KEY,
    rule_id NVARCHAR(100) NOT NULL UNIQUE, -- e.g., 'MA000120_PEN_001'
    award_code NVARCHAR(50) NOT NULL,
    rule_name NVARCHAR(500) NOT NULL,
    rule_description NVARCHAR(2000) NULL,
    priority INT NOT NULL DEFAULT 100, -- Lower number = higher priority
    status NVARCHAR(20) NOT NULL DEFAULT 'Active', -- Active, Inactive, Draft
    
    -- JSON condition (IF/WHEN clauses)
    condition_json NVARCHAR(MAX) NULL, -- JSON object with conditions
    
    -- JSON action (THEN clause)
    action_json NVARCHAR(MAX) NOT NULL, -- JSON object with multiplier/flat amounts
    
    -- Complete rule as JSON (for export/backup)
    full_rule_json NVARCHAR(MAX) NULL,
    
    -- Effective dates
    effective_from DATE NOT NULL,
    effective_to DATE NULL,
    
    -- FWC clause reference
    clause_reference NVARCHAR(200) NULL,
    clause_description NVARCHAR(1000) NULL,
    
    -- Metadata
    is_active BIT NOT NULL DEFAULT 1,
    created_at DATETIME2 DEFAULT GETUTCDATE(),
    updated_at DATETIME2 DEFAULT GETUTCDATE(),
    created_by NVARCHAR(100) DEFAULT 'SYSTEM',
    updated_by NVARCHAR(100) DEFAULT 'SYSTEM',
    
    -- Validation
    CONSTRAINT chk_penalty_rules_json CHECK (ISJSON(condition_json) = 1 OR condition_json IS NULL),
    CONSTRAINT chk_action_json CHECK (ISJSON(action_json) = 1)
);
GO

CREATE INDEX ix_tblpenaltyrulesJson_award ON TblPenaltyRulesJSON(award_code);
GO

CREATE INDEX ix_tblpenaltyrulesJson_rule_id ON TblPenaltyRulesJSON(rule_id);
GO

CREATE INDEX ix_tblpenaltyrulesJson_priority ON TblPenaltyRulesJSON(award_code, priority, status);
GO

CREATE INDEX ix_tblpenaltyrulesJson_active ON TblPenaltyRulesJSON(is_active, effective_from, effective_to);
GO

-- =============================================
-- Allowance Rules Table (JSON-based)
-- Stores award-specific allowance rules with JSON conditions
-- =============================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='TblAllowanceRulesJSON' AND xtype='U')
CREATE TABLE TblAllowanceRulesJSON (
    id INT IDENTITY(1,1) PRIMARY KEY,
    rule_id NVARCHAR(100) NOT NULL UNIQUE, -- e.g., 'MA000120_ALW_001'
    award_code NVARCHAR(50) NOT NULL,
    rule_name NVARCHAR(500) NOT NULL,
    rule_description NVARCHAR(2000) NULL,
    priority INT NOT NULL DEFAULT 100,
    status NVARCHAR(20) NOT NULL DEFAULT 'Active',
    
    -- JSON condition
    condition_json NVARCHAR(MAX) NULL,
    
    -- JSON action (allowance amount, frequency)
    action_json NVARCHAR(MAX) NOT NULL,
    
    -- Complete rule as JSON
    full_rule_json NVARCHAR(MAX) NULL,
    
    -- Effective dates
    effective_from DATE NOT NULL,
    effective_to DATE NULL,
    
    -- FWC clause reference
    clause_reference NVARCHAR(200) NULL,
    clause_description NVARCHAR(1000) NULL,
    
    -- Metadata
    is_active BIT NOT NULL DEFAULT 1,
    created_at DATETIME2 DEFAULT GETUTCDATE(),
    updated_at DATETIME2 DEFAULT GETUTCDATE(),
    created_by NVARCHAR(100) DEFAULT 'SYSTEM',
    updated_by NVARCHAR(100) DEFAULT 'SYSTEM',
    
    -- Validation
    CONSTRAINT chk_allowance_condition_json CHECK (ISJSON(condition_json) = 1 OR condition_json IS NULL),
    CONSTRAINT chk_allowance_action_json CHECK (ISJSON(action_json) = 1)
);
GO

CREATE INDEX ix_tblallowancerulesJson_award ON TblAllowanceRulesJSON(award_code);
GO

CREATE INDEX ix_tblallowancerulesJson_rule_id ON TblAllowanceRulesJSON(rule_id);
GO

CREATE INDEX ix_tblallowancerulesJson_priority ON TblAllowanceRulesJSON(award_code, priority, status);
GO

-- =============================================
-- Rule Execution Log
-- Tracks which rules were evaluated and applied
-- =============================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='TblRuleExecutionHistory' AND xtype='U')
CREATE TABLE TblRuleExecutionHistory (
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    rule_id NVARCHAR(100) NOT NULL,
    award_code NVARCHAR(50) NOT NULL,
    classification_fixed_id INT NULL,
    base_rate DECIMAL(18,4) NULL,
    
    -- Execution context
    employment_type NVARCHAR(50) NULL,
    day_of_week NVARCHAR(20) NULL,
    shift_start_time TIME NULL,
    shift_end_time TIME NULL,
    employee_age INT NULL,
    overtime_hours DECIMAL(5,2) NULL,
    
    -- Rule evaluation
    condition_met BIT NOT NULL,
    rule_applied BIT NOT NULL,
    
    -- Calculation result
    multiplier_applied DECIMAL(5,4) NULL,
    flat_amount_applied DECIMAL(10,2) NULL,
    calculated_rate DECIMAL(18,4) NULL,
    calculation_note NVARCHAR(1000) NULL,
    
    -- Timing
    executed_at DATETIME2 DEFAULT GETUTCDATE(),
    execution_duration_ms INT NULL,
    
    -- User context
    executed_by NVARCHAR(100) DEFAULT 'SYSTEM'
);
GO

CREATE INDEX ix_tblruleexechistory_rule ON TblRuleExecutionHistory(rule_id);
GO

CREATE INDEX ix_tblruleexechistory_award ON TblRuleExecutionHistory(award_code);
GO

CREATE INDEX ix_tblruleexechistory_date ON TblRuleExecutionHistory(executed_at);
GO

-- =============================================
-- Sample Data for MA000120
-- Insert penalty rules from the provided JSON sample
-- =============================================

-- Casual Loading
INSERT INTO TblPenaltyRulesJSON (
    rule_id, award_code, rule_name, priority, status,
    condition_json, action_json, full_rule_json,
    effective_from, clause_reference
)
VALUES (
    'MA000120_PEN_001',
    'MA000120',
    'Casual Loading',
    50,
    'Active',
    '{"employment_type": ["Casual"]}',
    '{"apply_multiplier": 1.25, "apply_to": ["hourly_rate"], "note": "25% casual loading"}',
    '{"rule_id": "MA000120_PEN_001", "award_code": "MA000120", "name": "Casual Loading", "priority": 50, "status": "Active", "if": {"employment_type": ["Casual"]}, "then": {"apply_multiplier": 1.25, "apply_to": ["hourly_rate"], "note": "25% casual loading"}}',
    '2024-01-01',
    'Clause 10.4'
);

-- Saturday Ordinary Hours
INSERT INTO TblPenaltyRulesJSON (
    rule_id, award_code, rule_name, priority, status,
    condition_json, action_json, full_rule_json,
    effective_from, clause_reference
)
VALUES (
    'MA000120_PEN_002',
    'MA000120',
    'Saturday Ordinary Hours',
    100,
    'Active',
    '{"day_of_week": ["Saturday"], "start_time": "00:00", "end_time": "23:59"}',
    '{"apply_multiplier": 1.5, "apply_to": ["hourly_rate"], "note": "Saturday ordinary hours penalty"}',
    '{"rule_id": "MA000120_PEN_002", "award_code": "MA000120", "name": "Saturday Ordinary Hours", "priority": 100, "status": "Active", "when": {"day_of_week": ["Saturday"], "start_time": "00:00", "end_time": "23:59"}, "then": {"apply_multiplier": 1.5, "apply_to": ["hourly_rate"], "note": "Saturday ordinary hours penalty"}}',
    '2024-01-01',
    'Clause 25.5(a)'
);

-- Saturday Overtime First 2 Hours
INSERT INTO TblPenaltyRulesJSON (
    rule_id, award_code, rule_name, priority, status,
    condition_json, action_json, full_rule_json,
    effective_from, clause_reference
)
VALUES (
    'MA000120_PEN_003',
    'MA000120',
    'Saturday Overtime First 2 Hours',
    110,
    'Active',
    '{"day_of_week": ["Saturday"], "overtime_hours": {"lte": 2}}',
    '{"apply_multiplier": 1.5, "apply_to": ["overtime"], "note": "First two hours overtime Saturday"}',
    '{"rule_id": "MA000120_PEN_003", "award_code": "MA000120", "name": "Saturday Overtime First 2 Hours", "priority": 110, "status": "Active", "when": {"day_of_week": ["Saturday"]}, "if": {"overtime_hours": {"lte": 2}}, "then": {"apply_multiplier": 1.5, "apply_to": ["overtime"], "note": "First two hours overtime Saturday"}}',
    '2024-01-01',
    'Clause 28.2(a)'
);

-- Saturday Overtime After 2 Hours
INSERT INTO TblPenaltyRulesJSON (
    rule_id, award_code, rule_name, priority, status,
    condition_json, action_json, full_rule_json,
    effective_from, clause_reference
)
VALUES (
    'MA000120_PEN_004',
    'MA000120',
    'Saturday Overtime After 2 Hours',
    120,
    'Active',
    '{"day_of_week": ["Saturday"], "overtime_hours": {"gt": 2}}',
    '{"apply_multiplier": 2.0, "apply_to": ["overtime"], "note": "Overtime beyond two hours Saturday"}',
    '{"rule_id": "MA000120_PEN_004", "award_code": "MA000120", "name": "Saturday Overtime After 2 Hours", "priority": 120, "status": "Active", "when": {"day_of_week": ["Saturday"]}, "if": {"overtime_hours": {"gt": 2}}, "then": {"apply_multiplier": 2.0, "apply_to": ["overtime"], "note": "Overtime beyond two hours Saturday"}}',
    '2024-01-01',
    'Clause 28.2(b)'
);

-- Sunday All Hours
INSERT INTO TblPenaltyRulesJSON (
    rule_id, award_code, rule_name, priority, status,
    condition_json, action_json, full_rule_json,
    effective_from, clause_reference
)
VALUES (
    'MA000120_PEN_005',
    'MA000120',
    'Sunday All Hours',
    130,
    'Active',
    '{"day_of_week": ["Sunday"]}',
    '{"apply_multiplier": 2.0, "apply_to": ["hourly_rate", "overtime"], "note": "Sunday penalty"}',
    '{"rule_id": "MA000120_PEN_005", "award_code": "MA000120", "name": "Sunday All Hours", "priority": 130, "status": "Active", "when": {"day_of_week": ["Sunday"]}, "then": {"apply_multiplier": 2.0, "apply_to": ["hourly_rate", "overtime"], "note": "Sunday penalty"}}',
    '2024-01-01',
    'Clause 25.5(b)'
);

-- Public Holiday
INSERT INTO TblPenaltyRulesJSON (
    rule_id, award_code, rule_name, priority, status,
    condition_json, action_json, full_rule_json,
    effective_from, clause_reference
)
VALUES (
    'MA000120_PEN_006',
    'MA000120',
    'Public Holiday',
    200,
    'Active',
    '{"day_type": ["public_holiday"]}',
    '{"apply_multiplier": 2.5, "apply_to": ["hourly_rate", "overtime"], "note": "Public holiday penalty"}',
    '{"rule_id": "MA000120_PEN_006", "award_code": "MA000120", "name": "Public Holiday", "priority": 200, "status": "Active", "when": {"day_type": ["public_holiday"]}, "then": {"apply_multiplier": 2.5, "apply_to": ["hourly_rate", "overtime"], "note": "Public holiday penalty"}}',
    '2024-01-01',
    'Clause 29.2'
);

-- Night Shift (10pm - 7am)
INSERT INTO TblPenaltyRulesJSON (
    rule_id, award_code, rule_name, priority, status,
    condition_json, action_json, full_rule_json,
    effective_from, clause_reference
)
VALUES (
    'MA000120_PEN_007',
    'MA000120',
    'Night Shift Penalty',
    90,
    'Active',
    '{"shift_type": ["night"], "time_range": {"start": "22:00", "end": "07:00"}}',
    '{"apply_multiplier": 1.15, "apply_to": ["hourly_rate"], "note": "Night shift 15% penalty (10pm-7am)"}',
    '{"rule_id": "MA000120_PEN_007", "award_code": "MA000120", "name": "Night Shift Penalty", "priority": 90, "status": "Active", "when": {"shift_type": ["night"], "time_range": {"start": "22:00", "end": "07:00"}}, "then": {"apply_multiplier": 1.15, "apply_to": ["hourly_rate"], "note": "Night shift 15% penalty (10pm-7am)"}}',
    '2024-01-01',
    'Clause 25.7'
);

-- Evening Shift (Afternoon)
INSERT INTO TblPenaltyRulesJSON (
    rule_id, award_code, rule_name, priority, status,
    condition_json, action_json, full_rule_json,
    effective_from, clause_reference
)
VALUES (
    'MA000120_PEN_008',
    'MA000120',
    'Evening Shift Penalty',
    85,
    'Active',
    '{"shift_type": ["afternoon", "evening"], "time_range": {"start": "18:00", "end": "22:00"}}',
    '{"apply_multiplier": 1.125, "apply_to": ["hourly_rate"], "note": "Evening shift 12.5% penalty (6pm-10pm)"}',
    '{"rule_id": "MA000120_PEN_008", "award_code": "MA000120", "name": "Evening Shift Penalty", "priority": 85, "status": "Active", "when": {"shift_type": ["afternoon", "evening"], "time_range": {"start": "18:00", "end": "22:00"}}, "then": {"apply_multiplier": 1.125, "apply_to": ["hourly_rate"], "note": "Evening shift 12.5% penalty (6pm-10pm)"}}',
    '2024-01-01',
    'Clause 25.6'
);

-- Weekday Overtime - First 2 Hours
INSERT INTO TblPenaltyRulesJSON (
    rule_id, award_code, rule_name, priority, status,
    condition_json, action_json, full_rule_json,
    effective_from, clause_reference
)
VALUES (
    'MA000120_PEN_009',
    'MA000120',
    'Weekday Overtime First 2 Hours',
    105,
    'Active',
    '{"day_of_week": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"], "overtime_hours": {"lte": 2}}',
    '{"apply_multiplier": 1.5, "apply_to": ["overtime"], "note": "First two hours overtime Monday-Friday"}',
    '{"rule_id": "MA000120_PEN_009", "award_code": "MA000120", "name": "Weekday Overtime First 2 Hours", "priority": 105, "status": "Active", "when": {"day_of_week": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]}, "if": {"overtime_hours": {"lte": 2}}, "then": {"apply_multiplier": 1.5, "apply_to": ["overtime"], "note": "First two hours overtime Monday-Friday"}}',
    '2024-01-01',
    'Clause 28.1(a)'
);

-- Weekday Overtime - After 2 Hours
INSERT INTO TblPenaltyRulesJSON (
    rule_id, award_code, rule_name, priority, status,
    condition_json, action_json, full_rule_json,
    effective_from, clause_reference
)
VALUES (
    'MA000120_PEN_010',
    'MA000120',
    'Weekday Overtime After 2 Hours',
    115,
    'Active',
    '{"day_of_week": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"], "overtime_hours": {"gt": 2}}',
    '{"apply_multiplier": 2.0, "apply_to": ["overtime"], "note": "Overtime beyond two hours Monday-Friday"}',
    '{"rule_id": "MA000120_PEN_010", "award_code": "MA000120", "name": "Weekday Overtime After 2 Hours", "priority": 115, "status": "Active", "when": {"day_of_week": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]}, "if": {"overtime_hours": {"gt": 2}}, "then": {"apply_multiplier": 2.0, "apply_to": ["overtime"], "note": "Overtime beyond two hours Monday-Friday"}}',
    '2024-01-01',
    'Clause 28.1(b)'
);

GO

-- =============================================
-- Sample Allowance Rules for MA000120
-- =============================================

-- Meal Allowance (shift > 5 hours, ends after 7pm)
INSERT INTO TblAllowanceRulesJSON (
    rule_id, award_code, rule_name, priority, status,
    condition_json, action_json, full_rule_json,
    effective_from, clause_reference
)
VALUES (
    'MA000120_ALW_001',
    'MA000120',
    'Meal Allowance - Late Finish',
    100,
    'Active',
    '{"shift_duration_hours": {"gte": 5}, "shift_end_time": {"gte": "19:00"}}',
    '{"apply_flat_amount": 17.07, "frequency": "per_shift", "note": "Meal allowance for shift > 5 hours ending after 7pm"}',
    '{"rule_id": "MA000120_ALW_001", "award_code": "MA000120", "name": "Meal Allowance - Late Finish", "priority": 100, "status": "Active", "if": {"shift_duration_hours": {"gte": 5}, "shift_end_time": {"gte": "19:00"}}, "then": {"apply_flat_amount": 17.07, "frequency": "per_shift", "note": "Meal allowance for shift > 5 hours ending after 7pm"}}',
    '2024-01-01',
    'Clause 20.2(a)'
);

-- Sleepover Allowance
INSERT INTO TblAllowanceRulesJSON (
    rule_id, award_code, rule_name, priority, status,
    condition_json, action_json, full_rule_json,
    effective_from, clause_reference
)
VALUES (
    'MA000120_ALW_002',
    'MA000120',
    'Sleepover Allowance',
    110,
    'Active',
    '{"shift_type": ["sleepover"]}',
    '{"apply_flat_amount": 63.99, "frequency": "per_night", "note": "Sleepover shift allowance"}',
    '{"rule_id": "MA000120_ALW_002", "award_code": "MA000120", "name": "Sleepover Allowance", "priority": 110, "status": "Active", "if": {"shift_type": ["sleepover"]}, "then": {"apply_flat_amount": 63.99, "frequency": "per_night", "note": "Sleepover shift allowance"}}',
    '2024-01-01',
    'Clause 25.8'
);

-- First Aid Allowance
INSERT INTO TblAllowanceRulesJSON (
    rule_id, award_code, rule_name, priority, status,
    condition_json, action_json, full_rule_json,
    effective_from, clause_reference
)
VALUES (
    'MA000120_ALW_003',
    'MA000120',
    'First Aid Allowance',
    120,
    'Active',
    '{"has_first_aid_certificate": true, "is_first_aid_officer": true}',
    '{"apply_flat_amount": 1.54, "frequency": "per_shift", "note": "First aid officer allowance"}',
    '{"rule_id": "MA000120_ALW_003", "award_code": "MA000120", "name": "First Aid Allowance", "priority": 120, "status": "Active", "if": {"has_first_aid_certificate": true, "is_first_aid_officer": true}, "then": {"apply_flat_amount": 1.54, "frequency": "per_shift", "note": "First aid officer allowance"}}',
    '2024-01-01',
    'Clause 20.5'
);

GO

PRINT 'JSON-based penalty rules tables created successfully';
PRINT 'Sample penalty and allowance rules for MA000120 inserted';
PRINT 'Total penalty rules: 10';
PRINT 'Total allowance rules: 3';
PRINT 'Ready for rule engine integration';
GO
