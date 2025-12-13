using Dapper;
using RuleEngine.Application.Commands.ApplyRule;
using RuleEngine.Application.Commands.CompileAwardsSummary;
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

    public async Task<bool> InitializeBasicRulesAsync()
    {
        using var connection = _context.CreateConnection();
        
        var result = await connection.QueryFirstOrDefaultAsync<dynamic>(
            "sp_InitializeBasicRules",
            commandType: System.Data.CommandType.StoredProcedure
        );

        return result?.Status == "Success";
    }
}
