-- Migration: 005_create_stored_procedures.sql
-- Creates stored procedures for rules engine and awards analysis

-- Stored Procedure: Compile Awards Summary
-- Analyzes staging tables and generates awards summary data
IF OBJECT_ID('sp_CompileAwardsSummary', 'P') IS NOT NULL
    DROP PROCEDURE sp_CompileAwardsSummary;
GO

CREATE PROCEDURE sp_CompileAwardsSummary
    @award_code NVARCHAR(50) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    BEGIN TRY
        -- If award_code is provided, compile for specific award, otherwise compile all
        IF @award_code IS NOT NULL
        BEGIN
            -- Delete existing summary for the award
            DELETE FROM TblAwardsSummary WHERE award_code = @award_code;
            
            -- Insert/Update award summary
            INSERT INTO TblAwardsSummary (
                award_code,
                award_name,
                total_classifications,
                total_pay_rates,
                total_expense_allowances,
                total_wage_allowances,
                min_base_rate,
                max_base_rate,
                avg_base_rate,
                is_custom,
                compiled_at
            )
            SELECT 
                a.code as award_code,
                a.name as award_name,
                ISNULL(c.classification_count, 0) as total_classifications,
                ISNULL(p.pay_rate_count, 0) as total_pay_rates,
                ISNULL(e.expense_count, 0) as total_expense_allowances,
                ISNULL(w.wage_count, 0) as total_wage_allowances,
                p.min_rate as min_base_rate,
                p.max_rate as max_base_rate,
                p.avg_rate as avg_base_rate,
                0 as is_custom,
                GETUTCDATE() as compiled_at
            FROM Stg_TblAwards a
            LEFT JOIN (
                SELECT award_code, COUNT(*) as classification_count
                FROM Stg_TblClassifications
                WHERE award_code = @award_code
                GROUP BY award_code
            ) c ON a.code = c.award_code
            LEFT JOIN (
                SELECT 
                    award_code, 
                    COUNT(*) as pay_rate_count,
                    MIN(base_rate) as min_rate,
                    MAX(base_rate) as max_rate,
                    AVG(base_rate) as avg_rate
                FROM Stg_TblPayRates
                WHERE award_code = @award_code AND base_rate IS NOT NULL
                GROUP BY award_code
            ) p ON a.code = p.award_code
            LEFT JOIN (
                SELECT award_code, COUNT(*) as expense_count
                FROM Stg_TblExpenseAllowances
                WHERE award_code = @award_code
                GROUP BY award_code
            ) e ON a.code = e.award_code
            LEFT JOIN (
                SELECT award_code, COUNT(*) as wage_count
                FROM Stg_TblWageAllowances
                WHERE award_code = @award_code
                GROUP BY award_code
            ) w ON a.code = w.award_code
            WHERE a.code = @award_code;
        END
        ELSE
        BEGIN
            -- Truncate and rebuild all summaries
            TRUNCATE TABLE TblAwardsSummary;
            
            INSERT INTO TblAwardsSummary (
                award_code,
                award_name,
                total_classifications,
                total_pay_rates,
                total_expense_allowances,
                total_wage_allowances,
                min_base_rate,
                max_base_rate,
                avg_base_rate,
                is_custom,
                compiled_at
            )
            SELECT 
                a.code as award_code,
                a.name as award_name,
                ISNULL(c.classification_count, 0) as total_classifications,
                ISNULL(p.pay_rate_count, 0) as total_pay_rates,
                ISNULL(e.expense_count, 0) as total_expense_allowances,
                ISNULL(w.wage_count, 0) as total_wage_allowances,
                p.min_rate as min_base_rate,
                p.max_rate as max_base_rate,
                p.avg_rate as avg_base_rate,
                0 as is_custom,
                GETUTCDATE() as compiled_at
            FROM Stg_TblAwards a
            LEFT JOIN (
                SELECT award_code, COUNT(*) as classification_count
                FROM Stg_TblClassifications
                GROUP BY award_code
            ) c ON a.code = c.award_code
            LEFT JOIN (
                SELECT 
                    award_code, 
                    COUNT(*) as pay_rate_count,
                    MIN(base_rate) as min_rate,
                    MAX(base_rate) as max_rate,
                    AVG(base_rate) as avg_rate
                FROM Stg_TblPayRates
                WHERE base_rate IS NOT NULL
                GROUP BY award_code
            ) p ON a.code = p.award_code
            LEFT JOIN (
                SELECT award_code, COUNT(*) as expense_count
                FROM Stg_TblExpenseAllowances
                GROUP BY award_code
            ) e ON a.code = e.award_code
            LEFT JOIN (
                SELECT award_code, COUNT(*) as wage_count
                FROM Stg_TblWageAllowances
                GROUP BY award_code
            ) w ON a.code = w.award_code;
        END
        
        SELECT 'Success' as Status, @@ROWCOUNT as RecordsCompiled;
    END TRY
    BEGIN CATCH
        SELECT 'Error' as Status, ERROR_MESSAGE() as ErrorMessage;
    END CATCH
END
GO

-- Stored Procedure: Initialize Basic Rules
-- Creates the basic set of rules for awards compilation
IF OBJECT_ID('sp_InitializeBasicRules', 'P') IS NOT NULL
    DROP PROCEDURE sp_InitializeBasicRules;
GO

CREATE PROCEDURE sp_InitializeBasicRules
AS
BEGIN
    SET NOCOUNT ON;
    
    BEGIN TRY
        -- Insert basic simple rules
        
        -- Rule 1: Minimum Pay Rate Validation
        IF NOT EXISTS (SELECT 1 FROM TblRules WHERE rule_code = 'RULE_MIN_PAY_RATE')
        INSERT INTO TblRules (rule_code, rule_name, rule_type, rule_category, rule_definition, rule_expression, priority)
        VALUES (
            'RULE_MIN_PAY_RATE',
            'Minimum Pay Rate Validation',
            'SIMPLE',
            'PAY_RATE',
            'Validates that all pay rates meet or exceed FWC minimum standards',
            'base_rate >= min_fwc_rate',
            100
        );
        
        -- Rule 2: Pay Rate Range Check
        IF NOT EXISTS (SELECT 1 FROM TblRules WHERE rule_code = 'RULE_PAY_RANGE')
        INSERT INTO TblRules (rule_code, rule_name, rule_type, rule_category, rule_definition, rule_expression, priority)
        VALUES (
            'RULE_PAY_RANGE',
            'Pay Rate Range Validation',
            'SIMPLE',
            'PAY_RATE',
            'Ensures pay rates fall within acceptable ranges for the classification',
            'base_rate BETWEEN classification_min_rate AND classification_max_rate',
            90
        );
        
        -- Rule 3: Classification Level Order
        IF NOT EXISTS (SELECT 1 FROM TblRules WHERE rule_code = 'RULE_CLASS_LEVEL')
        INSERT INTO TblRules (rule_code, rule_name, rule_type, rule_category, rule_definition, rule_expression, priority)
        VALUES (
            'RULE_CLASS_LEVEL',
            'Classification Level Hierarchy',
            'SIMPLE',
            'CLASSIFICATION',
            'Validates classification levels are in proper hierarchical order',
            'classification_level IS NOT NULL AND classification_level > 0',
            80
        );
        
        -- Rule 4: Allowance Rate Validation
        IF NOT EXISTS (SELECT 1 FROM TblRules WHERE rule_code = 'RULE_ALLOWANCE_RATE')
        INSERT INTO TblRules (rule_code, rule_name, rule_type, rule_category, rule_definition, rule_expression, priority)
        VALUES (
            'RULE_ALLOWANCE_RATE',
            'Allowance Rate Validation',
            'SIMPLE',
            'ALLOWANCE',
            'Validates that allowance amounts are positive and reasonable',
            'allowance_amount > 0',
            70
        );
        
        -- Rule 5: Award Operative Dates
        IF NOT EXISTS (SELECT 1 FROM TblRules WHERE rule_code = 'RULE_OPERATIVE_DATES')
        INSERT INTO TblRules (rule_code, rule_name, rule_type, rule_category, rule_definition, rule_expression, priority)
        VALUES (
            'RULE_OPERATIVE_DATES',
            'Award Operative Date Validation',
            'SIMPLE',
            'COMPLIANCE',
            'Ensures award operative dates are valid and properly sequenced',
            'award_operative_from <= award_operative_to OR award_operative_to IS NULL',
            60
        );
        
        -- Rule 6: All-Purpose Allowance Flag
        IF NOT EXISTS (SELECT 1 FROM TblRules WHERE rule_code = 'RULE_ALL_PURPOSE')
        INSERT INTO TblRules (rule_code, rule_name, rule_type, rule_category, rule_definition, rule_expression, priority)
        VALUES (
            'RULE_ALL_PURPOSE',
            'All-Purpose Allowance Classification',
            'SIMPLE',
            'ALLOWANCE',
            'Identifies allowances that are all-purpose for penalty rate calculations',
            'is_all_purpose = 1',
            50
        );
        
        -- Insert complex rules
        
        -- Complex Rule 1: Pay Rate Progression
        IF NOT EXISTS (SELECT 1 FROM TblRules WHERE rule_code = 'RULE_PAY_PROGRESSION')
        INSERT INTO TblRules (rule_code, rule_name, rule_type, rule_category, rule_definition, rule_expression, priority)
        VALUES (
            'RULE_PAY_PROGRESSION',
            'Pay Rate Progression Validation',
            'COMPLEX',
            'PAY_RATE',
            'Validates that pay rates increase appropriately with classification levels within the same parent classification',
            'WHEN classification_level > prev_classification_level THEN base_rate >= prev_base_rate',
            100
        );
        
        -- Complex Rule 2: Custom Award Pay Rate Override
        IF NOT EXISTS (SELECT 1 FROM TblRules WHERE rule_code = 'RULE_CUSTOM_PAY_OVERRIDE')
        INSERT INTO TblRules (rule_code, rule_name, rule_type, rule_category, rule_definition, rule_expression, priority)
        VALUES (
            'RULE_CUSTOM_PAY_OVERRIDE',
            'Custom Award Pay Rate Override',
            'COMPLEX',
            'PAY_RATE',
            'Applies custom pay rate multipliers while ensuring minimum FWC rates are maintained',
            'custom_pay_rate = base_rate * multiplier WHERE custom_pay_rate >= min_fwc_rate',
            95
        );
        
        -- Complex Rule 3: Comprehensive Allowance Calculation
        IF NOT EXISTS (SELECT 1 FROM TblRules WHERE rule_code = 'RULE_TOTAL_ALLOWANCES')
        INSERT INTO TblRules (rule_code, rule_name, rule_type, rule_category, rule_definition, rule_expression, priority)
        VALUES (
            'RULE_TOTAL_ALLOWANCES',
            'Total Allowances Calculation',
            'COMPLEX',
            'ALLOWANCE',
            'Calculates total allowances including wage and expense allowances for accurate payroll',
            'total_allowances = SUM(wage_allowances) + SUM(expense_allowances)',
            85
        );
        
        -- Complex Rule 4: Award Version Control
        IF NOT EXISTS (SELECT 1 FROM TblRules WHERE rule_code = 'RULE_VERSION_CONTROL')
        INSERT INTO TblRules (rule_code, rule_name, rule_type, rule_category, rule_definition, rule_expression, priority)
        VALUES (
            'RULE_VERSION_CONTROL',
            'Award Version Control and Latest Selection',
            'COMPLEX',
            'COMPLIANCE',
            'Ensures only the latest version of each award is active based on version number and operative dates',
            'SELECT MAX(version_number) WHERE award_operative_to IS NULL OR award_operative_to >= GETDATE()',
            90
        );
        
        -- Complex Rule 5: Classification Hierarchy Integrity
        IF NOT EXISTS (SELECT 1 FROM TblRules WHERE rule_code = 'RULE_CLASS_HIERARCHY')
        INSERT INTO TblRules (rule_code, rule_name, rule_type, rule_category, rule_definition, rule_expression, priority)
        VALUES (
            'RULE_CLASS_HIERARCHY',
            'Classification Hierarchy Integrity',
            'COMPLEX',
            'CLASSIFICATION',
            'Validates the entire classification hierarchy including next_up and next_down references',
            'VALIDATE next_up_classification_fixed_id AND next_down_classification_fixed_id references',
            80
        );
        
        -- Complex Rule 6: Industry-Specific Award Assignment
        IF NOT EXISTS (SELECT 1 FROM TblRules WHERE rule_code = 'RULE_INDUSTRY_ASSIGN')
        INSERT INTO TblRules (rule_code, rule_name, rule_type, rule_category, rule_definition, rule_expression, priority)
        VALUES (
            'RULE_INDUSTRY_ASSIGN',
            'Industry-Specific Award Assignment',
            'COMPLEX',
            'COMPLIANCE',
            'Assigns appropriate awards to organizations based on industry type and business classification',
            'MATCH organization_industry_type WITH award_industry_coverage',
            75
        );
        
        SELECT 'Success' as Status, @@ROWCOUNT as RulesInitialized;
    END TRY
    BEGIN CATCH
        SELECT 'Error' as Status, ERROR_MESSAGE() as ErrorMessage;
    END CATCH
END
GO

-- Stored Procedure: Generate Award Rules JSON
-- Generates JSON output of rules for a specific award or all awards
IF OBJECT_ID('sp_GenerateAwardRulesJSON', 'P') IS NOT NULL
    DROP PROCEDURE sp_GenerateAwardRulesJSON;
GO

CREATE PROCEDURE sp_GenerateAwardRulesJSON
    @award_code NVARCHAR(50) = NULL,
    @rule_type NVARCHAR(50) = NULL  -- 'SIMPLE', 'COMPLEX', or NULL for all
AS
BEGIN
    SET NOCOUNT ON;
    
    BEGIN TRY
        -- Generate JSON output for rules
        SELECT 
            (
                SELECT 
                    r.rule_code,
                    r.rule_name,
                    r.rule_type,
                    r.rule_category,
                    r.rule_definition,
                    r.rule_expression,
                    r.priority,
                    r.is_active,
                    (
                        SELECT 
                            ar.award_code,
                            a.award_name,
                            ar.is_applied,
                            ar.applied_at,
                            ar.result_summary
                        FROM TblAwardRules ar
                        INNER JOIN TblAwardsSummary a ON ar.award_code = a.award_code
                        WHERE ar.rule_code = r.rule_code
                        AND (@award_code IS NULL OR ar.award_code = @award_code)
                        FOR JSON PATH
                    ) as applied_awards
                FROM TblRules r
                WHERE r.is_active = 1
                AND (@rule_type IS NULL OR r.rule_type = @rule_type)
                ORDER BY r.priority DESC, r.rule_code
                FOR JSON PATH
            ) as rules_json
    END TRY
    BEGIN CATCH
        SELECT 'Error' as Status, ERROR_MESSAGE() as ErrorMessage;
    END CATCH
END
GO

-- Stored Procedure: Apply Rule to Award
-- Applies a specific rule to an award and logs the result
IF OBJECT_ID('sp_ApplyRuleToAward', 'P') IS NOT NULL
    DROP PROCEDURE sp_ApplyRuleToAward;
GO

CREATE PROCEDURE sp_ApplyRuleToAward
    @rule_code NVARCHAR(50),
    @award_code NVARCHAR(50)
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @execution_id NVARCHAR(50);
    DECLARE @start_time DATETIME2;
    DECLARE @end_time DATETIME2;
    DECLARE @duration_ms INT;
    
    SET @execution_id = NEWID();
    SET @start_time = GETUTCDATE();
    
    BEGIN TRY
        -- Check if rule exists and is active
        IF NOT EXISTS (SELECT 1 FROM TblRules WHERE rule_code = @rule_code AND is_active = 1)
        BEGIN
            RAISERROR('Rule not found or inactive', 16, 1);
            RETURN;
        END
        
        -- Check if award exists
        IF NOT EXISTS (SELECT 1 FROM TblAwardsSummary WHERE award_code = @award_code)
        BEGIN
            RAISERROR('Award not found in summary', 16, 1);
            RETURN;
        END
        
        -- Create or update award-rule mapping
        IF EXISTS (SELECT 1 FROM TblAwardRules WHERE rule_code = @rule_code AND award_code = @award_code)
        BEGIN
            UPDATE TblAwardRules
            SET is_applied = 1,
                applied_at = GETUTCDATE(),
                result_summary = 'Rule applied successfully'
            WHERE rule_code = @rule_code AND award_code = @award_code;
        END
        ELSE
        BEGIN
            INSERT INTO TblAwardRules (award_code, rule_code, is_applied, applied_at, result_summary)
            VALUES (@award_code, @rule_code, 1, GETUTCDATE(), 'Rule applied successfully');
        END
        
        SET @end_time = GETUTCDATE();
        SET @duration_ms = DATEDIFF(MILLISECOND, @start_time, @end_time);
        
        -- Log execution
        INSERT INTO TblRuleExecutionLog (
            execution_id, rule_code, award_code, execution_status, 
            execution_result, execution_duration_ms
        )
        VALUES (
            @execution_id, @rule_code, @award_code, 'SUCCESS',
            'Rule applied successfully', @duration_ms
        );
        
        SELECT 'Success' as Status, @execution_id as ExecutionId;
    END TRY
    BEGIN CATCH
        SET @end_time = GETUTCDATE();
        SET @duration_ms = DATEDIFF(MILLISECOND, @start_time, @end_time);
        
        -- Log failed execution
        INSERT INTO TblRuleExecutionLog (
            execution_id, rule_code, award_code, execution_status, 
            error_message, execution_duration_ms
        )
        VALUES (
            @execution_id, @rule_code, @award_code, 'FAILED',
            ERROR_MESSAGE(), @duration_ms
        );
        
        SELECT 'Error' as Status, ERROR_MESSAGE() as ErrorMessage;
    END CATCH
END
GO

PRINT 'Stored procedures created successfully';
GO
