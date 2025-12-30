using Dapper;
using RuleEngine.Application.Commands.ApplyRule;
using RuleEngine.Application.Commands.CompileAwardsSummary;
using RuleEngine.Application.Commands.CompileAwardsDetailed;
using RuleEngine.Application.Commands.CalculatePayRates;
using RuleEngine.Application.Interfaces;
using RuleEngine.Domain.Entities;
using RuleEngine.Infrastructure.Data;

namespace RuleEngine.Infrastructure.Repositories;

public class RuleEngineRepository : IRuleEngineRepository
{
    private readonly DatabaseContext _context;

    public RuleEngineRepository(DatabaseContext context)
    {
        _context = context;
    }

    public async Task<CompileAwardsSummaryResult> CompileAwardsSummaryAsync(string? awardCode)
    {
        using var connection = _context.CreateConnection();
        var parameters = new { award_code = awardCode };
        
        var result = await connection.QueryFirstOrDefaultAsync<dynamic>(
            "sp_CompileAwardsSummary",
            parameters,
            commandType: System.Data.CommandType.StoredProcedure
        );

        return new CompileAwardsSummaryResult
        {
            Status = result?.Status ?? "Error",
            RecordsCompiled = result?.RecordsCompiled ?? 0,
            ErrorMessage = result?.ErrorMessage
        };
    }

    public async Task<CompileAwardsDetailedResult> CompileAwardsDetailedAsync(string? awardCode)
    {
        using var connection = _context.CreateConnection();
        var parameters = new { award_code = awardCode };
        
        var result = await connection.QueryFirstOrDefaultAsync<dynamic>(
            "sp_CompileAwardsDetailed",
            parameters,
            commandType: System.Data.CommandType.StoredProcedure
        );

        return new CompileAwardsDetailedResult
        {
            Status = result?.Status ?? "Error",
            TotalRecords = result?.TotalRecords ?? 0,
            TotalAwards = result?.TotalAwards ?? 0,
            BaseRecords = result?.BaseRecords ?? 0,
            ClassificationRecords = result?.ClassificationRecords ?? 0,
            PayRateRecords = result?.PayRateRecords ?? 0,
            ExpenseRecords = result?.ExpenseRecords ?? 0,
            WageRecords = result?.WageRecords ?? 0,
            ErrorMessage = result?.ErrorMessage
        };
    }

    public async Task<ApplyRuleResult> ApplyRuleToAwardAsync(string ruleCode, string awardCode)
    {
        using var connection = _context.CreateConnection();
        var parameters = new { rule_code = ruleCode, award_code = awardCode };
        
        var result = await connection.QueryFirstOrDefaultAsync<dynamic>(
            "sp_ApplyRuleToAward",
            parameters,
            commandType: System.Data.CommandType.StoredProcedure
        );

        return new ApplyRuleResult
        {
            Status = result?.Status ?? "Error",
            ExecutionId = result?.ExecutionId ?? string.Empty,
            ErrorMessage = result?.ErrorMessage
        };
    }

    public async Task<IEnumerable<Award>> GetAwardsAsync(string? awardCode, string? industryType, bool? isActive)
    {
        using var connection = _context.CreateConnection();
        
        var sql = @"
            SELECT 
                id as Id,
                award_code as AwardCode,
                award_name as AwardName,
                industry_type as IndustryType,
                total_classifications as TotalClassifications,
                total_pay_rates as TotalPayRates,
                total_expense_allowances as TotalExpenseAllowances,
                total_wage_allowances as TotalWageAllowances,
                min_base_rate as MinBaseRate,
                max_base_rate as MaxBaseRate,
                avg_base_rate as AvgBaseRate,
                is_custom as IsCustom,
                is_active as IsActive,
                compiled_at as CompiledAt,
                created_at as CreatedAt,
                updated_at as UpdatedAt
            FROM TblAwardsSummary
            WHERE (@AwardCode IS NULL OR award_code = @AwardCode)
            AND (@IndustryType IS NULL OR industry_type = @IndustryType)
            AND (@IsActive IS NULL OR is_active = @IsActive)
            ORDER BY award_code";

        return await connection.QueryAsync<Award>(sql, new { AwardCode = awardCode, IndustryType = industryType, IsActive = isActive });
    }

    public async Task<IEnumerable<Rule>> GetRulesAsync(string? ruleType, string? ruleCategory, bool? isActive)
    {
        using var connection = _context.CreateConnection();
        
        var sql = @"
            SELECT 
                id as Id,
                rule_code as RuleCode,
                rule_name as RuleName,
                rule_type as RuleType,
                rule_category as RuleCategory,
                rule_definition as RuleDefinition,
                rule_expression as RuleExpression,
                priority as Priority,
                is_active as IsActive,
                created_by as CreatedBy,
                created_at as CreatedAt,
                updated_at as UpdatedAt
            FROM TblRules
            WHERE (@RuleType IS NULL OR rule_type = @RuleType)
            AND (@RuleCategory IS NULL OR rule_category = @RuleCategory)
            AND (@IsActive IS NULL OR is_active = @IsActive)
            ORDER BY priority DESC, rule_code";

        return await connection.QueryAsync<Rule>(sql, new { RuleType = ruleType, RuleCategory = ruleCategory, IsActive = isActive });
    }

    public async Task<string> GenerateAwardRulesJsonAsync(string? awardCode, string? ruleType)
    {
        using var connection = _context.CreateConnection();
        var parameters = new { award_code = awardCode, rule_type = ruleType };
        
        var result = await connection.QueryFirstOrDefaultAsync<dynamic>(
            "sp_GenerateAwardRulesJSON",
            parameters,
            commandType: System.Data.CommandType.StoredProcedure
        );

        return result?.rules_json ?? "[]";
    }

    public async Task<IEnumerable<AwardDetailed>> GetAwardsDetailedAsync(string? awardCode, string? recordType, int? classificationFixedId)
    {
        using var connection = _context.CreateConnection();
        
        var sql = @"
            SELECT 
                id as Id,
                award_code as AwardCode,
                award_name as AwardName,
                award_id as AwardId,
                award_fixed_id as AwardFixedId,
                award_operative_from as AwardOperativeFrom,
                award_operative_to as AwardOperativeTo,
                version_number as VersionNumber,
                published_year as PublishedYear,
                classification_fixed_id as ClassificationFixedId,
                classification_name as ClassificationName,
                parent_classification_name as ParentClassificationName,
                classification_level as ClassificationLevel,
                classification_clauses as ClassificationClauses,
                classification_clause_description as ClassificationClauseDescription,
                base_pay_rate_id as BasePayRateId,
                base_rate_type as BaseRateType,
                base_rate as BaseRate,
                calculated_pay_rate_id as CalculatedPayRateId,
                calculated_rate_type as CalculatedRateType,
                calculated_rate as CalculatedRate,
                employee_rate_type_code as EmployeeRateTypeCode,
                expense_allowance_fixed_id as ExpenseAllowanceFixedId,
                expense_clause_fixed_id as ExpenseClauseFixedId,
                expense_clauses as ExpenseClauses,
                expense_allowance_name as ExpenseAllowanceName,
                parent_expense_allowance as ParentExpenseAllowance,
                expense_allowance_amount as ExpenseAllowanceAmount,
                expense_payment_frequency as ExpensePaymentFrequency,
                expense_is_all_purpose as ExpenseIsAllPurpose,
                expense_last_adjusted_year as ExpenseLastAdjustedYear,
                expense_cpi_quarter as ExpenseCpiQuarter,
                wage_allowance_fixed_id as WageAllowanceFixedId,
                wage_clause_fixed_id as WageClauseFixedId,
                wage_clauses as WageClauses,
                wage_allowance_name as WageAllowanceName,
                parent_wage_allowance as ParentWageAllowance,
                wage_allowance_rate as WageAllowanceRate,
                wage_allowance_rate_unit as WageAllowanceRateUnit,
                wage_allowance_amount as WageAllowanceAmount,
                wage_payment_frequency as WagePaymentFrequency,
                wage_is_all_purpose as WageIsAllPurpose,
                record_type as RecordType,
                is_active as IsActive,
                compiled_at as CompiledAt,
                created_at as CreatedAt,
                updated_at as UpdatedAt
            FROM TblAwardsDetailed
            WHERE (@AwardCode IS NULL OR award_code = @AwardCode)
            AND (@RecordType IS NULL OR record_type = @RecordType)
            AND (@ClassificationFixedId IS NULL OR classification_fixed_id = @ClassificationFixedId)
            ORDER BY award_code, record_type, id";

        return await connection.QueryAsync<AwardDetailed>(sql, new { 
            AwardCode = awardCode, 
            RecordType = recordType, 
            ClassificationFixedId = classificationFixedId 
        });
    }

    public async Task<bool> InitializeBasicRulesAsync()
    {
        using var connection = _context.CreateConnection();
        
        var result = await connection.QueryFirstOrDefaultAsync<dynamic>(
            "sp_InitializeBasicRules",
            commandType: System.Data.CommandType.StoredProcedure
        );

        return result?.Status == "Success";
    }

    public async Task<CalculatePayRatesResult> CalculateAllPayRatesAsync(string? awardCode, int? classificationFixedId)
    {
        using var connection = _context.CreateConnection();
        var parameters = new
        {
            award_code = awardCode,
            classification_fixed_id = classificationFixedId
        };
        
        var result = await connection.QueryFirstOrDefaultAsync<dynamic>(
            "sp_CalculateAllPayRates",
            parameters,
            commandType: System.Data.CommandType.StoredProcedure,
            commandTimeout: 300 // 5 minutes for large calculations
        );

        return new CalculatePayRatesResult
        {
            Status = result?.Status ?? "Error",
            TotalRecordsCreated = result?.TotalRecordsCreated ?? 0,
            DurationSeconds = result?.DurationSeconds ?? 0,
            AwardsProcessed = result?.AwardsProcessed ?? 0,
            ClassificationsProcessed = result?.ClassificationsProcessed ?? 0,
            FullTimeRates = result?.FullTimeRates ?? 0,
            PartTimeRates = result?.PartTimeRates ?? 0,
            CasualRates = result?.CasualRates ?? 0,
            Message = result?.Status == "Success" 
                ? $"Successfully calculated {result?.TotalRecordsCreated ?? 0} pay rates" 
                : "Calculation failed"
        };
    }

    public async Task<IEnumerable<CalculatedPayRate>> GetCalculatedPayRatesAsync(
        string? awardCode,
        int? classificationFixedId,
        string? employmentType,
        string? dayType,
        string? shiftType,
        string? employeeAgeCategory,
        int pageNumber,
        int pageSize)
    {
        using var connection = _context.CreateConnection();
        
        var sql = @"
            SELECT 
                id AS Id,
                award_code AS AwardCode,
                award_name AS AwardName,
                classification_fixed_id AS ClassificationFixedId,
                classification_name AS ClassificationName,
                classification_level AS ClassificationLevel,
                base_pay_rate_id AS BasePayRateId,
                base_rate AS BaseRate,
                base_rate_type AS BaseRateType,
                employment_type AS EmploymentType,
                employee_age_category AS EmployeeAgeCategory,
                employee_category AS EmployeeCategory,
                day_type AS DayType,
                shift_type AS ShiftType,
                time_range AS TimeRange,
                casual_loading_applied AS CasualLoadingApplied,
                casual_loaded_rate AS CasualLoadedRate,
                junior_percentage_applied AS JuniorPercentageApplied,
                junior_adjusted_rate AS JuniorAdjustedRate,
                apprentice_percentage_applied AS ApprenticePercentageApplied,
                apprentice_adjusted_rate AS ApprenticeAdjustedRate,
                penalty_type AS PenaltyType,
                penalty_multiplier_applied AS PenaltyMultiplierApplied,
                penalty_flat_amount_applied AS PenaltyFlatAmountApplied,
                calculated_hourly_rate AS CalculatedHourlyRate,
                calculated_rate_description AS CalculatedRateDescription,
                calculation_steps AS CalculationSteps,
                applicable_allowance_ids AS ApplicableAllowanceIds,
                applicable_allowance_total AS ApplicableAllowanceTotal,
                effective_from AS EffectiveFrom,
                effective_to AS EffectiveTo,
                penalty_clause_reference AS PenaltyClauseReference,
                casual_clause_reference AS CasualClauseReference,
                junior_clause_reference AS JuniorClauseReference,
                is_active AS IsActive,
                compiled_at AS CompiledAt,
                compiled_by AS CompiledBy,
                created_at AS CreatedAt,
                updated_at AS UpdatedAt
            FROM TblCalculatedPayRates
            WHERE is_active = 1
                AND (@award_code IS NULL OR award_code = @award_code)
                AND (@classification_fixed_id IS NULL OR classification_fixed_id = @classification_fixed_id)
                AND (@employment_type IS NULL OR employment_type = @employment_type)
                AND (@day_type IS NULL OR day_type = @day_type)
                AND (@shift_type IS NULL OR shift_type = @shift_type)
                AND (@employee_age_category IS NULL OR employee_age_category = @employee_age_category)
            ORDER BY 
                award_code,
                classification_level,
                employment_type,
                day_type,
                shift_type,
                employee_age_category
            OFFSET @offset ROWS
            FETCH NEXT @pageSize ROWS ONLY";
        
        var parameters = new
        {
            award_code = awardCode,
            classification_fixed_id = classificationFixedId,
            employment_type = employmentType,
            day_type = dayType,
            shift_type = shiftType,
            employee_age_category = employeeAgeCategory,
            offset = (pageNumber - 1) * pageSize,
            pageSize
        };

        return await connection.QueryAsync<CalculatedPayRate>(sql, parameters);
    }

    public async Task<(List<Penalty> penalties, int totalCount)> GetPenaltiesAsync(
        string? awardCode,
        int? classificationLevel,
        string? penaltyType,
        int pageNumber,
        int pageSize)
    {
        using var connection = _context.CreateConnection();
        
        var sql = @"
            SELECT 
                id AS Id,
                penalty_fixed_id AS PenaltyFixedId,
                award_code AS AwardCode,
                penalty_description AS PenaltyDescription,
                rate AS Rate,
                penalty_calculated_value AS PenaltyCalculatedValue,
                classification_level AS ClassificationLevel,
                clause_fixed_id AS ClauseFixedId,
                clause_description AS ClauseDescription,
                base_pay_rate_id AS BasePayRateId,
                operative_from AS OperativeFrom,
                operative_to AS OperativeTo,
                version_number AS VersionNumber,
                published_year AS PublishedYear,
                created_at AS CreatedAt,
                updated_at AS UpdatedAt
            FROM Stg_TblPenalties
            WHERE (@award_code IS NULL OR award_code = @award_code)
                AND (@classification_level IS NULL OR classification_level = @classification_level)
            ORDER BY 
                award_code,
                classification_level,
                penalty_fixed_id
            OFFSET @offset ROWS
            FETCH NEXT @pageSize ROWS ONLY";

        var countSql = @"
            SELECT COUNT(*)
            FROM Stg_TblPenalties
            WHERE (@award_code IS NULL OR award_code = @award_code)
                AND (@classification_level IS NULL OR classification_level = @classification_level)";
        
        var parameters = new
        {
            award_code = awardCode,
            classification_level = classificationLevel,
            offset = (pageNumber - 1) * pageSize,
            pageSize
        };

        var penalties = await connection.QueryAsync<Penalty>(sql, parameters);
        var totalCount = await connection.ExecuteScalarAsync<int>(countSql, parameters);

        return (penalties.ToList(), totalCount);
    }

    public async Task<Rule> CreateRuleAsync(Rule rule)
    {
        using var connection = _context.CreateConnection();

        var sql = @"
            INSERT INTO TblRules 
            (rule_code, rule_name, rule_type, rule_category, priority, is_active, created_by, rule_expression, rule_definition, created_at, updated_at)
            VALUES 
            (@rule_code, @rule_name, @rule_type, @rule_category, @priority, @is_active, @created_by, @rule_expression, @rule_definition, @created_at, @updated_at);
            
            SELECT CAST(SCOPE_IDENTITY() as int);";

        var parameters = new
        {
            rule_code = rule.RuleCode,
            rule_name = rule.RuleName,
            rule_type = rule.RuleType,
            rule_category = rule.RuleCategory,
            priority = rule.Priority,
            is_active = rule.IsActive,
            created_by = rule.CreatedBy,
            rule_expression = rule.RuleExpression,
            rule_definition = rule.RuleDefinition,
            created_at = rule.CreatedAt,
            updated_at = rule.UpdatedAt
        };

        var id = await connection.QuerySingleAsync<int>(sql, parameters);
        rule.Id = id;
        return rule;
    }
}

