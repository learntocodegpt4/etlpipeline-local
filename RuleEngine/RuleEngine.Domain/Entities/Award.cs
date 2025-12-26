namespace RuleEngine.Domain.Entities;

public class Award
{
    public int Id { get; set; }
    public string AwardCode { get; set; } = string.Empty;
    public string AwardName { get; set; } = string.Empty;
    public string? IndustryType { get; set; }
    public int TotalClassifications { get; set; }
    public int TotalPayRates { get; set; }
    public int TotalExpenseAllowances { get; set; }
    public int TotalWageAllowances { get; set; }
    public decimal? MinBaseRate { get; set; }
    public decimal? MaxBaseRate { get; set; }
    public decimal? AvgBaseRate { get; set; }
    public bool IsCustom { get; set; }
    public bool IsActive { get; set; }
    public DateTime CompiledAt { get; set; }
    public DateTime CreatedAt { get; set; }
    public DateTime UpdatedAt { get; set; }
}
