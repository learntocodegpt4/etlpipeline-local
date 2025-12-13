namespace RuleEngine.Domain.Entities;

public class AwardRule
{
    public int Id { get; set; }
    public string AwardCode { get; set; } = string.Empty;
    public string RuleCode { get; set; } = string.Empty;
    public bool IsApplied { get; set; }
    public DateTime? AppliedAt { get; set; }
    public string? ResultSummary { get; set; }
    public DateTime CreatedAt { get; set; }
}
