namespace RuleEngine.Domain.Entities;

public class AwardDetailed
{
    public int Id { get; set; }
    
    // Award Basic Info
    public string AwardCode { get; set; } = string.Empty;
    public string? AwardName { get; set; }
    public int? AwardId { get; set; }
    public int? AwardFixedId { get; set; }
    public DateTime? AwardOperativeFrom { get; set; }
    public DateTime? AwardOperativeTo { get; set; }
    public int? VersionNumber { get; set; }
    public int? PublishedYear { get; set; }
    
    // Classification Info
    public int? ClassificationFixedId { get; set; }
    public string? ClassificationName { get; set; }
    public string? ParentClassificationName { get; set; }
    public int? ClassificationLevel { get; set; }
    public string? ClassificationClauses { get; set; }
    public string? ClassificationClauseDescription { get; set; }
    
    // Pay Rate Info
    public string? BasePayRateId { get; set; }
    public string? BaseRateType { get; set; }
    public decimal? BaseRate { get; set; }
    public string? CalculatedPayRateId { get; set; }
    public string? CalculatedRateType { get; set; }
    public decimal? CalculatedRate { get; set; }
    public string? EmployeeRateTypeCode { get; set; }
    
    // Expense Allowance Info
    public int? ExpenseAllowanceFixedId { get; set; }
    public int? ExpenseClauseFixedId { get; set; }
    public string? ExpenseClauses { get; set; }
    public string? ExpenseAllowanceName { get; set; }
    public string? ParentExpenseAllowance { get; set; }
    public decimal? ExpenseAllowanceAmount { get; set; }
    public string? ExpensePaymentFrequency { get; set; }
    public bool? ExpenseIsAllPurpose { get; set; }
    public int? ExpenseLastAdjustedYear { get; set; }
    public string? ExpenseCpiQuarter { get; set; }
    
    // Wage Allowance Info
    public int? WageAllowanceFixedId { get; set; }
    public int? WageClauseFixedId { get; set; }
    public string? WageClauses { get; set; }
    public string? WageAllowanceName { get; set; }
    public string? ParentWageAllowance { get; set; }
    public decimal? WageAllowanceRate { get; set; }
    public string? WageAllowanceRateUnit { get; set; }
    public decimal? WageAllowanceAmount { get; set; }
    public string? WagePaymentFrequency { get; set; }
    public bool? WageIsAllPurpose { get; set; }
    
    // Metadata
    public string RecordType { get; set; } = string.Empty;
    public bool IsActive { get; set; }
    public DateTime CompiledAt { get; set; }
    public DateTime CreatedAt { get; set; }
    public DateTime UpdatedAt { get; set; }
}
