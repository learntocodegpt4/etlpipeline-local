-- Migration: 009_create_json_rule_engine_sp.sql
-- Creates stored procedures for JSON-based rule engine
-- Evaluates penalty and allowance rules with complex conditions
-- Run against MS SQL Server

-- =============================================
-- Stored Procedure: Evaluate and Apply JSON Penalty Rules
-- Processes JSON-based penalty rules and calculates rates
-- =============================================
IF OBJECT_ID('sp_EvaluateJSONPenaltyRules', 'P') IS NOT NULL
    DROP PROCEDURE sp_EvaluateJSONPenaltyRules;
GO

CREATE PROCEDURE sp_EvaluateJSONPenaltyRules
    @award_code NVARCHAR(50),
    @classification_fixed_id INT = NULL,
    @base_rate DECIMAL(18,4),
    @employment_type NVARCHAR(50) = 'FULL_TIME', -- FULL_TIME, PART_TIME, CASUAL
    @day_of_week NVARCHAR(20) = 'Monday', -- Monday, Tuesday, ..., Sunday
    @day_type NVARCHAR(50) = 'weekday', -- weekday, weekend, public_holiday
    @shift_type NVARCHAR(50) = 'standard', -- standard, night, afternoon, evening, sleepover
    @shift_start_time TIME = '09:00',
    @shift_end_time TIME = '17:00',
    @shift_duration_hours DECIMAL(5,2) = 8.0,
    @overtime_hours DECIMAL(5,2) = 0,
    @employee_age INT = 25,
    @is_first_aid_officer BIT = 0,
    @return_details BIT = 1 -- Return detailed breakdown
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @start_time DATETIME = GETUTCDATE();
    DECLARE @calculated_rate DECIMAL(18,4) = @base_rate;
    DECLARE @total_multiplier DECIMAL(5,4) = 1.0;
    DECLARE @total_flat_amount DECIMAL(10,2) = 0;
    DECLARE @calculation_steps NVARCHAR(MAX) = 'Base: $' + CAST(@base_rate AS NVARCHAR(20));
    DECLARE @rules_applied INT = 0;
    
    -- Temporary table to store applicable rules
    CREATE TABLE #ApplicableRules (
        rule_id NVARCHAR(100),
        rule_name NVARCHAR(500),
        priority INT,
        multiplier DECIMAL(5,4),
        flat_amount DECIMAL(10,2),
        apply_to NVARCHAR(100),
        note NVARCHAR(1000)
    );
    
    -- =============================================
    -- Step 1: Find applicable penalty rules
    -- =============================================
    
    -- Casual Loading Rule
    IF @employment_type = 'CASUAL'
    BEGIN
        INSERT INTO #ApplicableRules (rule_id, rule_name, priority, multiplier, apply_to, note)
        SELECT 
            rule_id,
            rule_name,
            priority,
            CAST(JSON_VALUE(action_json, '$.apply_multiplier') AS DECIMAL(5,4)),
            NULL,
            JSON_VALUE(action_json, '$.apply_to'),
            JSON_VALUE(action_json, '$.note')
        FROM TblPenaltyRulesJSON
        WHERE award_code = @award_code
            AND status = 'Active'
            AND is_active = 1
            AND GETDATE() BETWEEN effective_from AND ISNULL(effective_to, '9999-12-31')
            AND JSON_VALUE(condition_json, '$.employment_type[0]') = 'Casual';
    END
    
    -- Day of Week Rules (Saturday, Sunday)
    IF @day_of_week IN ('Saturday', 'Sunday')
    BEGIN
        INSERT INTO #ApplicableRules (rule_id, rule_name, priority, multiplier, apply_to, note)
        SELECT 
            rule_id,
            rule_name,
            priority,
            CAST(JSON_VALUE(action_json, '$.apply_multiplier') AS DECIMAL(5,4)),
            NULL,
            JSON_VALUE(action_json, '$.apply_to'),
            JSON_VALUE(action_json, '$.note')
        FROM TblPenaltyRulesJSON
        WHERE award_code = @award_code
            AND status = 'Active'
            AND is_active = 1
            AND GETDATE() BETWEEN effective_from AND ISNULL(effective_to, '9999-12-31')
            AND (
                JSON_VALUE(condition_json, '$.day_of_week[0]') = @day_of_week
                OR JSON_VALUE(condition_json, '$.day_of_week') LIKE '%' + @day_of_week + '%'
            )
            AND (@overtime_hours = 0 OR condition_json NOT LIKE '%overtime_hours%');
    END
    
    -- Public Holiday Rules
    IF @day_type = 'public_holiday'
    BEGIN
        INSERT INTO #ApplicableRules (rule_id, rule_name, priority, multiplier, apply_to, note)
        SELECT 
            rule_id,
            rule_name,
            priority,
            CAST(JSON_VALUE(action_json, '$.apply_multiplier') AS DECIMAL(5,4)),
            NULL,
            JSON_VALUE(action_json, '$.apply_to'),
            JSON_VALUE(action_json, '$.note')
        FROM TblPenaltyRulesJSON
        WHERE award_code = @award_code
            AND status = 'Active'
            AND is_active = 1
            AND GETDATE() BETWEEN effective_from AND ISNULL(effective_to, '9999-12-31')
            AND JSON_VALUE(condition_json, '$.day_type[0]') = 'public_holiday';
    END
    
    -- Shift Type Rules (Night, Evening)
    IF @shift_type IN ('night', 'evening', 'afternoon')
    BEGIN
        INSERT INTO #ApplicableRules (rule_id, rule_name, priority, multiplier, apply_to, note)
        SELECT 
            rule_id,
            rule_name,
            priority,
            CAST(JSON_VALUE(action_json, '$.apply_multiplier') AS DECIMAL(5,4)),
            NULL,
            JSON_VALUE(action_json, '$.apply_to'),
            JSON_VALUE(action_json, '$.note')
        FROM TblPenaltyRulesJSON
        WHERE award_code = @award_code
            AND status = 'Active'
            AND is_active = 1
            AND GETDATE() BETWEEN effective_from AND ISNULL(effective_to, '9999-12-31')
            AND (
                JSON_VALUE(condition_json, '$.shift_type[0]') = @shift_type
                OR JSON_VALUE(condition_json, '$.shift_type') LIKE '%' + @shift_type + '%'
            );
    END
    
    -- Overtime Rules
    IF @overtime_hours > 0
    BEGIN
        -- First 2 hours overtime
        IF @overtime_hours <= 2
        BEGIN
            INSERT INTO #ApplicableRules (rule_id, rule_name, priority, multiplier, apply_to, note)
            SELECT 
                rule_id,
                rule_name,
                priority,
                CAST(JSON_VALUE(action_json, '$.apply_multiplier') AS DECIMAL(5,4)),
                NULL,
                JSON_VALUE(action_json, '$.apply_to'),
                JSON_VALUE(action_json, '$.note')
            FROM TblPenaltyRulesJSON
            WHERE award_code = @award_code
                AND status = 'Active'
                AND is_active = 1
                AND GETDATE() BETWEEN effective_from AND ISNULL(effective_to, '9999-12-31')
                AND condition_json LIKE '%overtime_hours%'
                AND condition_json LIKE '%lte%';
        END
        ELSE
        BEGIN
            -- After 2 hours overtime
            INSERT INTO #ApplicableRules (rule_id, rule_name, priority, multiplier, apply_to, note)
            SELECT 
                rule_id,
                rule_name,
                priority,
                CAST(JSON_VALUE(action_json, '$.apply_multiplier') AS DECIMAL(5,4)),
                NULL,
                JSON_VALUE(action_json, '$.apply_to'),
                JSON_VALUE(action_json, '$.note')
            FROM TblPenaltyRulesJSON
            WHERE award_code = @award_code
                AND status = 'Active'
                AND is_active = 1
                AND GETDATE() BETWEEN effective_from AND ISNULL(effective_to, '9999-12-31')
                AND condition_json LIKE '%overtime_hours%'
                AND condition_json LIKE '%gt%';
        END
    END
    
    -- =============================================
    -- Step 2: Apply rules in priority order
    -- =============================================
    
    DECLARE @rule_cursor CURSOR;
    DECLARE @curr_rule_id NVARCHAR(100);
    DECLARE @curr_rule_name NVARCHAR(500);
    DECLARE @curr_multiplier DECIMAL(5,4);
    DECLARE @curr_note NVARCHAR(1000);
    
    SET @rule_cursor = CURSOR FOR
    SELECT rule_id, rule_name, multiplier, note
    FROM #ApplicableRules
    ORDER BY priority ASC;
    
    OPEN @rule_cursor;
    FETCH NEXT FROM @rule_cursor INTO @curr_rule_id, @curr_rule_name, @curr_multiplier, @curr_note;
    
    WHILE @@FETCH_STATUS = 0
    BEGIN
        IF @curr_multiplier IS NOT NULL AND @curr_multiplier > 0
        BEGIN
            SET @calculated_rate = @calculated_rate * @curr_multiplier;
            SET @total_multiplier = @total_multiplier * @curr_multiplier;
            SET @calculation_steps = @calculation_steps + ' × ' + @curr_rule_name + ' ' + 
                CAST(@curr_multiplier AS NVARCHAR(10)) + ' = $' + CAST(@calculated_rate AS NVARCHAR(20));
            SET @rules_applied = @rules_applied + 1;
            
            -- Log rule execution
            INSERT INTO TblRuleExecutionHistory (
                rule_id, award_code, classification_fixed_id, base_rate,
                employment_type, day_of_week, shift_start_time, shift_end_time,
                employee_age, overtime_hours,
                condition_met, rule_applied, multiplier_applied, calculated_rate, calculation_note
            )
            VALUES (
                @curr_rule_id, @award_code, @classification_fixed_id, @base_rate,
                @employment_type, @day_of_week, @shift_start_time, @shift_end_time,
                @employee_age, @overtime_hours,
                1, 1, @curr_multiplier, @calculated_rate, @curr_note
            );
        END
        
        FETCH NEXT FROM @rule_cursor INTO @curr_rule_id, @curr_rule_name, @curr_multiplier, @curr_note;
    END
    
    CLOSE @rule_cursor;
    DEALLOCATE @rule_cursor;
    
    -- =============================================
    -- Step 3: Process Allowances
    -- =============================================
    
    CREATE TABLE #ApplicableAllowances (
        rule_id NVARCHAR(100),
        rule_name NVARCHAR(500),
        flat_amount DECIMAL(10,2),
        frequency NVARCHAR(50),
        note NVARCHAR(1000)
    );
    
    -- Meal Allowance (shift > 5 hours, ends after 7pm)
    IF @shift_duration_hours >= 5 AND @shift_end_time >= '19:00'
    BEGIN
        INSERT INTO #ApplicableAllowances (rule_id, rule_name, flat_amount, frequency, note)
        SELECT 
            rule_id,
            rule_name,
            CAST(JSON_VALUE(action_json, '$.apply_flat_amount') AS DECIMAL(10,2)),
            JSON_VALUE(action_json, '$.frequency'),
            JSON_VALUE(action_json, '$.note')
        FROM TblAllowanceRulesJSON
        WHERE award_code = @award_code
            AND status = 'Active'
            AND is_active = 1
            AND rule_id LIKE '%ALW%MEAL%';
    END
    
    -- Sleepover Allowance
    IF @shift_type = 'sleepover'
    BEGIN
        INSERT INTO #ApplicableAllowances (rule_id, rule_name, flat_amount, frequency, note)
        SELECT 
            rule_id,
            rule_name,
            CAST(JSON_VALUE(action_json, '$.apply_flat_amount') AS DECIMAL(10,2)),
            JSON_VALUE(action_json, '$.frequency'),
            JSON_VALUE(action_json, '$.note')
        FROM TblAllowanceRulesJSON
        WHERE award_code = @award_code
            AND status = 'Active'
            AND is_active = 1
            AND rule_id LIKE '%SLEEPOVER%';
    END
    
    -- First Aid Allowance
    IF @is_first_aid_officer = 1
    BEGIN
        INSERT INTO #ApplicableAllowances (rule_id, rule_name, flat_amount, frequency, note)
        SELECT 
            rule_id,
            rule_name,
            CAST(JSON_VALUE(action_json, '$.apply_flat_amount') AS DECIMAL(10,2)),
            JSON_VALUE(action_json, '$.frequency'),
            JSON_VALUE(action_json, '$.note')
        FROM TblAllowanceRulesJSON
        WHERE award_code = @award_code
            AND status = 'Active'
            AND is_active = 1
            AND rule_id LIKE '%FIRST_AID%';
    END
    
    -- Sum allowances
    SELECT @total_flat_amount = ISNULL(SUM(flat_amount), 0)
    FROM #ApplicableAllowances;
    
    IF @total_flat_amount > 0
    BEGIN
        SET @calculation_steps = @calculation_steps + ' + Allowances $' + CAST(@total_flat_amount AS NVARCHAR(20));
    END
    
    -- =============================================
    -- Step 4: Return Results
    -- =============================================
    
    IF @return_details = 1
    BEGIN
        SELECT 
            @award_code AS award_code,
            @base_rate AS base_rate,
            @employment_type AS employment_type,
            @day_of_week AS day_of_week,
            @day_type AS day_type,
            @shift_type AS shift_type,
            @calculated_rate AS calculated_hourly_rate,
            @total_multiplier AS total_multiplier_applied,
            @total_flat_amount AS total_allowances,
            @calculated_rate + @total_flat_amount AS total_compensation,
            @calculation_steps AS calculation_steps,
            @rules_applied AS rules_applied,
            DATEDIFF(MILLISECOND, @start_time, GETUTCDATE()) AS execution_time_ms;
        
        -- Return applied rules
        SELECT * FROM #ApplicableRules ORDER BY priority;
        
        -- Return applied allowances
        SELECT * FROM #ApplicableAllowances;
    END
    ELSE
    BEGIN
        SELECT 
            @calculated_rate AS calculated_hourly_rate,
            @total_flat_amount AS total_allowances,
            @calculated_rate + @total_flat_amount AS total_compensation;
    END
    
    -- Cleanup
    DROP TABLE #ApplicableRules;
    DROP TABLE #ApplicableAllowances;
END
GO

-- =============================================
-- Stored Procedure: Bulk Calculate Pay Rates Using JSON Rules
-- Generates all rate combinations using JSON penalty rules
-- =============================================
IF OBJECT_ID('sp_CalculatePayRatesFromJSONRules', 'P') IS NOT NULL
    DROP PROCEDURE sp_CalculatePayRatesFromJSONRules;
GO

CREATE PROCEDURE sp_CalculatePayRatesFromJSONRules
    @award_code NVARCHAR(50) = NULL,
    @classification_fixed_id INT = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @start_time DATETIME2 = GETUTCDATE();
    DECLARE @records_created INT = 0;
    
    BEGIN TRY
        -- Clear existing calculated rates for the award
        IF @award_code IS NOT NULL
        BEGIN
            DELETE FROM TblCalculatedPayRates 
            WHERE award_code = @award_code
                AND (@classification_fixed_id IS NULL OR classification_fixed_id = @classification_fixed_id);
        END
        
        -- =============================================
        -- Generate all combinations
        -- =============================================
        
        -- Cursor through pay rates
        DECLARE @curr_award_code NVARCHAR(50);
        DECLARE @curr_class_id INT;
        DECLARE @curr_class_name NVARCHAR(500);
        DECLARE @curr_base_rate DECIMAL(18,4);
        DECLARE @curr_rate_id NVARCHAR(50);
        
        DECLARE rate_cursor CURSOR FOR
        SELECT DISTINCT
            p.award_code,
            p.classification_fixed_id,
            p.classification,
            p.calculated_rate,
            p.calculated_pay_rate_id
        FROM Stg_TblPayRates p
        WHERE (@award_code IS NULL OR p.award_code = @award_code)
            AND (@classification_fixed_id IS NULL OR p.classification_fixed_id = @classification_fixed_id)
            AND p.calculated_rate IS NOT NULL
            AND p.calculated_rate > 0;
        
        OPEN rate_cursor;
        FETCH NEXT FROM rate_cursor INTO @curr_award_code, @curr_class_id, @curr_class_name, @curr_base_rate, @curr_rate_id;
        
        WHILE @@FETCH_STATUS = 0
        BEGIN
            -- Standard weekday scenarios
            EXEC sp_InsertCalculatedRateFromJSON 
                @curr_award_code, @curr_class_id, @curr_class_name, @curr_base_rate, @curr_rate_id,
                'FULL_TIME', 'ADULT', 'Monday', 'weekday', 'standard', '09:00', '17:00', 8.0, 0;
            
            EXEC sp_InsertCalculatedRateFromJSON 
                @curr_award_code, @curr_class_id, @curr_class_name, @curr_base_rate, @curr_rate_id,
                'PART_TIME', 'ADULT', 'Monday', 'weekday', 'standard', '09:00', '17:00', 8.0, 0;
            
            EXEC sp_InsertCalculatedRateFromJSON 
                @curr_award_code, @curr_class_id, @curr_class_name, @curr_base_rate, @curr_rate_id,
                'CASUAL', 'ADULT', 'Monday', 'weekday', 'standard', '09:00', '17:00', 8.0, 0;
            
            -- Saturday scenarios
            EXEC sp_InsertCalculatedRateFromJSON 
                @curr_award_code, @curr_class_id, @curr_class_name, @curr_base_rate, @curr_rate_id,
                'FULL_TIME', 'ADULT', 'Saturday', 'weekend', 'standard', '09:00', '17:00', 8.0, 0;
            
            EXEC sp_InsertCalculatedRateFromJSON 
                @curr_award_code, @curr_class_id, @curr_class_name, @curr_base_rate, @curr_rate_id,
                'CASUAL', 'ADULT', 'Saturday', 'weekend', 'standard', '09:00', '17:00', 8.0, 0;
            
            -- Sunday scenarios
            EXEC sp_InsertCalculatedRateFromJSON 
                @curr_award_code, @curr_class_id, @curr_class_name, @curr_base_rate, @curr_rate_id,
                'FULL_TIME', 'ADULT', 'Sunday', 'weekend', 'standard', '09:00', '17:00', 8.0, 0;
            
            EXEC sp_InsertCalculatedRateFromJSON 
                @curr_award_code, @curr_class_id, @curr_class_name, @curr_base_rate, @curr_rate_id,
                'CASUAL', 'ADULT', 'Sunday', 'weekend', 'standard', '09:00', '17:00', 8.0, 0;
            
            -- Public holiday
            EXEC sp_InsertCalculatedRateFromJSON 
                @curr_award_code, @curr_class_id, @curr_class_name, @curr_base_rate, @curr_rate_id,
                'FULL_TIME', 'ADULT', 'Monday', 'public_holiday', 'standard', '09:00', '17:00', 8.0, 0;
            
            -- Night shift
            EXEC sp_InsertCalculatedRateFromJSON 
                @curr_award_code, @curr_class_id, @curr_class_name, @curr_base_rate, @curr_rate_id,
                'FULL_TIME', 'ADULT', 'Monday', 'weekday', 'night', '22:00', '07:00', 8.0, 0;
            
            -- Evening shift
            EXEC sp_InsertCalculatedRateFromJSON 
                @curr_award_code, @curr_class_id, @curr_class_name, @curr_base_rate, @curr_rate_id,
                'FULL_TIME', 'ADULT', 'Monday', 'weekday', 'evening', '18:00', '22:00', 4.0, 0;
            
            SET @records_created = @records_created + 10;
            
            FETCH NEXT FROM rate_cursor INTO @curr_award_code, @curr_class_id, @curr_class_name, @curr_base_rate, @curr_rate_id;
        END
        
        CLOSE rate_cursor;
        DEALLOCATE rate_cursor;
        
        -- Log calculation
        DECLARE @duration_sec INT = DATEDIFF(SECOND, @start_time, GETUTCDATE());
        
        INSERT INTO TblPayCalculationLog (
            award_code, calculation_type, total_records_created,
            calculation_started_at, calculation_completed_at, calculation_duration_seconds,
            status, executed_by
        )
        VALUES (
            @award_code,
            CASE WHEN @award_code IS NULL THEN 'ALL_AWARDS' ELSE 'SINGLE_AWARD' END,
            @records_created,
            @start_time, GETUTCDATE(), @duration_sec,
            'SUCCESS', 'SYSTEM'
        );
        
        -- Return summary
        SELECT 
            'Success' AS Status,
            @award_code AS award_code,
            @records_created AS total_records_created,
            @duration_sec AS duration_seconds;
            
    END TRY
    BEGIN CATCH
        SELECT 'Error' AS Status, ERROR_MESSAGE() AS ErrorMessage;
    END CATCH
END
GO

-- =============================================
-- Helper Procedure: Insert Calculated Rate
-- =============================================
IF OBJECT_ID('sp_InsertCalculatedRateFromJSON', 'P') IS NOT NULL
    DROP PROCEDURE sp_InsertCalculatedRateFromJSON;
GO

CREATE PROCEDURE sp_InsertCalculatedRateFromJSON
    @award_code NVARCHAR(50),
    @class_id INT,
    @class_name NVARCHAR(500),
    @base_rate DECIMAL(18,4),
    @rate_id NVARCHAR(50),
    @emp_type NVARCHAR(50),
    @age_cat NVARCHAR(50),
    @day_of_week NVARCHAR(20),
    @day_type NVARCHAR(50),
    @shift_type NVARCHAR(50),
    @start_time TIME,
    @end_time TIME,
    @duration DECIMAL(5,2),
    @ot_hours DECIMAL(5,2)
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @calc_rate DECIMAL(18,4);
    DECLARE @calc_steps NVARCHAR(2000);
    DECLARE @total_mult DECIMAL(5,4);
    DECLARE @allowances DECIMAL(10,2);
    
    -- Call evaluation procedure
    CREATE TABLE #TempResult (
        award_code NVARCHAR(50),
        base_rate DECIMAL(18,4),
        employment_type NVARCHAR(50),
        day_of_week NVARCHAR(20),
        day_type NVARCHAR(50),
        shift_type NVARCHAR(50),
        calculated_hourly_rate DECIMAL(18,4),
        total_multiplier_applied DECIMAL(5,4),
        total_allowances DECIMAL(10,2),
        total_compensation DECIMAL(18,4),
        calculation_steps NVARCHAR(MAX),
        rules_applied INT,
        execution_time_ms INT
    );
    
    INSERT INTO #TempResult
    EXEC sp_EvaluateJSONPenaltyRules 
        @award_code, @class_id, @base_rate, @emp_type, @day_of_week, @day_type,
        @shift_type, @start_time, @end_time, @duration, @ot_hours, 25, 0, 1;
    
    SELECT 
        @calc_rate = calculated_hourly_rate,
        @calc_steps = calculation_steps,
        @total_mult = total_multiplier_applied,
        @allowances = total_allowances
    FROM #TempResult;
    
    -- Insert into TblCalculatedPayRates
    INSERT INTO TblCalculatedPayRates (
        award_code, classification_fixed_id, classification_name,
        base_pay_rate_id, base_rate, base_rate_type,
        employment_type, employee_age_category,
        day_type, shift_type,
        calculated_hourly_rate, calculation_steps,
        applicable_allowance_total,
        effective_from, is_active
    )
    VALUES (
        @award_code, @class_id, @class_name,
        @rate_id, @base_rate, 'HOURLY',
        @emp_type, @age_cat,
        @day_type, @shift_type,
        @calc_rate, @calc_steps,
        @allowances,
        GETDATE(), 1
    );
    
    DROP TABLE #TempResult;
END
GO

PRINT 'JSON rule engine stored procedures created successfully';
PRINT 'sp_EvaluateJSONPenaltyRules - Evaluate rules for single scenario';
PRINT 'sp_CalculatePayRatesFromJSONRules - Bulk calculate all combinations';
PRINT 'sp_InsertCalculatedRateFromJSON - Helper procedure for inserting rates';
GO
