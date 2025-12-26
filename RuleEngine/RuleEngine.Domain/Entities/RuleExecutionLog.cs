namespace RuleEngine.Domain.Entities;

public class RuleExecutionLog
{
    public int Id { get; set; }
    public string ExecutionId { get; set; } = string.Empty;
    public string RuleCode { get; set; } = string.Empty;
    public string? AwardCode { get; set; }
    public string ExecutionStatus { get; set; } = string.Empty;
    public string? ExecutionResult { get; set; }
    public string? ErrorMessage { get; set; }
    public int? ExecutionDurationMs { get; set; }
    public DateTime ExecutedAt { get; set; }
}
