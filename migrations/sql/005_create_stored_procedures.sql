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

-- Stored Procedure: Compile Awards Detailed
-- Compiles comprehensive award information with all combinations from staging tables
-- This provides maximum information for System Admin UI display and Tenant assignment
IF OBJECT_ID('sp_CompileAwardsDetailed', 'P') IS NOT NULL
    DROP PROCEDURE sp_CompileAwardsDetailed;
GO

CREATE PROCEDURE sp_CompileAwardsDetailed
    @award_code NVARCHAR(50) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    BEGIN TRY
        -- Clear existing data for the award(s) being compiled
        IF @award_code IS NOT NULL
        BEGIN
            DELETE FROM TblAwardsDetailed WHERE award_code = @award_code;
        END
        ELSE
        BEGIN
            TRUNCATE TABLE TblAwardsDetailed;
        END
        
        -- Insert comprehensive award data with all combinations
        -- This creates denormalized records showing all possible award configurations
        
        -- Step 1: Insert base award records (awards without any additional data)
        INSERT INTO TblAwardsDetailed (
            award_code, award_name, award_id, award_fixed_id,
            award_operative_from, award_operative_to, version_number, published_year,
            record_type, compiled_at
        )
        SELECT 
            a.code,
            a.name,
            a.award_id,
            a.award_fixed_id,
            a.award_operative_from,
            a.award_operative_to,
            a.version_number,
            a.published_year,
            'BASE' as record_type,
            GETUTCDATE() as compiled_at
        FROM Stg_TblAwards a
        WHERE (@award_code IS NULL OR a.code = @award_code);
        
        -- Step 2: Insert award + classification combinations
        INSERT INTO TblAwardsDetailed (
            award_code, award_name, award_id, award_fixed_id,
            award_operative_from, award_operative_to, version_number, published_year,
            classification_fixed_id, classification_name, parent_classification_name,
            classification_level, classification_clauses, classification_clause_description,
            record_type, compiled_at
        )
        SELECT 
            a.code,
            a.name,
            a.award_id,
            a.award_fixed_id,
            a.award_operative_from,
            a.award_operative_to,
            a.version_number,
            a.published_year,
            c.classification_fixed_id,
            c.classification,
            c.parent_classification_name,
            c.classification_level,
            c.clauses,
            c.clause_description,
            'WITH_CLASSIFICATION' as record_type,
            GETUTCDATE() as compiled_at
        FROM Stg_TblAwards a
        INNER JOIN Stg_TblClassifications c ON a.code = c.award_code
        WHERE (@award_code IS NULL OR a.code = @award_code);
        
        -- Step 3: Insert award + classification + pay rate combinations
        INSERT INTO TblAwardsDetailed (
            award_code, award_name, award_id, award_fixed_id,
            award_operative_from, award_operative_to, version_number, published_year,
            classification_fixed_id, classification_name, parent_classification_name,
            classification_level,
            base_pay_rate_id, base_rate_type, base_rate,
            calculated_pay_rate_id, calculated_rate_type, calculated_rate,
            employee_rate_type_code,
            record_type, compiled_at
        )
        SELECT 
            a.code,
            a.name,
            a.award_id,
            a.award_fixed_id,
            a.award_operative_from,
            a.award_operative_to,
            a.version_number,
            a.published_year,
            p.classification_fixed_id,
            p.classification,
            p.parent_classification_name,
            p.classification_level,
            p.base_pay_rate_id,
            p.base_rate_type,
            p.base_rate,
            p.calculated_pay_rate_id,
            p.calculated_rate_type,
            p.calculated_rate,
            p.employee_rate_type_code,
            'WITH_PAYRATE' as record_type,
            GETUTCDATE() as compiled_at
        FROM Stg_TblAwards a
        INNER JOIN Stg_TblPayRates p ON a.code = p.award_code
        WHERE (@award_code IS NULL OR a.code = @award_code);
        
        -- Step 4: Insert award + expense allowance combinations
        INSERT INTO TblAwardsDetailed (
            award_code, award_name, award_id, award_fixed_id,
            award_operative_from, award_operative_to, version_number, published_year,
            expense_allowance_fixed_id, expense_allowance_name, parent_expense_allowance,
            expense_allowance_amount, expense_payment_frequency, expense_is_all_purpose,
            expense_last_adjusted_year, expense_cpi_quarter,
            record_type, compiled_at
        )
        SELECT 
            a.code,
            a.name,
            a.award_id,
            a.award_fixed_id,
            a.award_operative_from,
            a.award_operative_to,
            a.version_number,
            a.published_year,
            e.expense_allowance_fixed_id,
            e.allowance,
            e.parent_allowance,
            e.allowance_amount,
            e.payment_frequency,
            e.is_all_purpose,
            e.last_adjusted_year,
            e.cpi_quarter_last_adjusted,
            'WITH_EXPENSE' as record_type,
            GETUTCDATE() as compiled_at
        FROM Stg_TblAwards a
        INNER JOIN Stg_TblExpenseAllowances e ON a.code = e.award_code
        WHERE (@award_code IS NULL OR a.code = @award_code);
        
        -- Step 5: Insert award + wage allowance combinations
        INSERT INTO TblAwardsDetailed (
            award_code, award_name, award_id, award_fixed_id,
            award_operative_from, award_operative_to, version_number, published_year,
            wage_allowance_fixed_id, wage_allowance_name, parent_wage_allowance,
            wage_allowance_rate, wage_allowance_rate_unit, wage_allowance_amount,
            wage_payment_frequency, wage_is_all_purpose,
            record_type, compiled_at
        )
        SELECT 
            a.code,
            a.name,
            a.award_id,
            a.award_fixed_id,
            a.award_operative_from,
            a.award_operative_to,
            a.version_number,
            a.published_year,
            w.wage_allowance_fixed_id,
            w.allowance,
            w.parent_allowance,
            w.rate,
            w.rate_unit,
            w.allowance_amount,
            w.payment_frequency,
            w.is_all_purpose,
            'WITH_WAGE' as record_type,
            GETUTCDATE() as compiled_at
        FROM Stg_TblAwards a
        INNER JOIN Stg_TblWageAllowances w ON a.code = w.award_code
        WHERE (@award_code IS NULL OR a.code = @award_code);
        
        -- Return summary of compilation
        SELECT 
            'Success' as Status,
            (SELECT COUNT(*) FROM TblAwardsDetailed WHERE @award_code IS NULL OR award_code = @award_code) as TotalRecords,
            (SELECT COUNT(DISTINCT award_code) FROM TblAwardsDetailed WHERE @award_code IS NULL OR award_code = @award_code) as TotalAwards,
            (SELECT COUNT(*) FROM TblAwardsDetailed WHERE record_type = 'BASE' AND (@award_code IS NULL OR award_code = @award_code)) as BaseRecords,
            (SELECT COUNT(*) FROM TblAwardsDetailed WHERE record_type = 'WITH_CLASSIFICATION' AND (@award_code IS NULL OR award_code = @award_code)) as ClassificationRecords,
            (SELECT COUNT(*) FROM TblAwardsDetailed WHERE record_type = 'WITH_PAYRATE' AND (@award_code IS NULL OR award_code = @award_code)) as PayRateRecords,
            (SELECT COUNT(*) FROM TblAwardsDetailed WHERE record_type = 'WITH_EXPENSE' AND (@award_code IS NULL OR award_code = @award_code)) as ExpenseRecords,
            (SELECT COUNT(*) FROM TblAwardsDetailed WHERE record_type = 'WITH_WAGE' AND (@award_code IS NULL OR award_code = @award_code)) as WageRecords;
            
    END TRY
    BEGIN CATCH
        SELECT 'Error' as Status, ERROR_MESSAGE() as ErrorMessage;
    END CATCH
END
GO

PRINT 'Stored procedures created successfully';
GO
