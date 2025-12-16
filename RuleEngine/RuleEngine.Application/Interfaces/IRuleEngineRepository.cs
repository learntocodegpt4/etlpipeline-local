using RuleEngine.Application.Commands.ApplyRule;
using RuleEngine.Application.Commands.CompileAwardsSummary;
using RuleEngine.Application.Commands.CompileAwardsDetailed;
using RuleEngine.Application.Commands.CalculatePayRates;
using RuleEngine.Domain.Entities;

namespace RuleEngine.Application.Interfaces;

public interface IRuleEngineRepository
{
    Task<CompileAwardsSummaryResult> CompileAwardsSummaryAsync(string? awardCode);
    Task<CompileAwardsDetailedResult> CompileAwardsDetailedAsync(string? awardCode);
    Task<ApplyRuleResult> ApplyRuleToAwardAsync(string ruleCode, string awardCode);
    Task<IEnumerable<Award>> GetAwardsAsync(string? awardCode, string? industryType, bool? isActive);
    Task<IEnumerable<AwardDetailed>> GetAwardsDetailedAsync(string? awardCode, string? recordType, int? classificationFixedId);
    Task<IEnumerable<Rule>> GetRulesAsync(string? ruleType, string? ruleCategory, bool? isActive);
    Task<string> GenerateAwardRulesJsonAsync(string? awardCode, string? ruleType);
    Task<bool> InitializeBasicRulesAsync();
    
    // Pay calculation methods
    Task<CalculatePayRatesResult> CalculateAllPayRatesAsync(string? awardCode, int? classificationFixedId);
    Task<IEnumerable<CalculatedPayRate>> GetCalculatedPayRatesAsync(
        string? awardCode,
        int? classificationFixedId,
        string? employmentType,
        string? dayType,
        string? shiftType,
        string? employeeAgeCategory,
        int pageNumber,
        int pageSize);
    
    // Penalties methods
    Task<(List<Penalty> penalties, int totalCount)> GetPenaltiesAsync(
        string? awardCode,
        int? classificationLevel,
        string? penaltyType,
        int pageNumber,
        int pageSize);
}
