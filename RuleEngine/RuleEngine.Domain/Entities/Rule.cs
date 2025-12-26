namespace RuleEngine.Domain.Entities;

public class Rule
{
    public int Id { get; set; }
    public string RuleCode { get; set; } = string.Empty;
    public string RuleName { get; set; } = string.Empty;
    public string RuleType { get; set; } = string.Empty;
    public string? RuleCategory { get; set; }
    public string RuleDefinition { get; set; } = string.Empty;
    public string? RuleExpression { get; set; }
    public int Priority { get; set; }
    public bool IsActive { get; set; }
    public string CreatedBy { get; set; } = "SYSTEM";
    public DateTime CreatedAt { get; set; }
    public DateTime UpdatedAt { get; set; }
}
