using MediatR;

namespace RuleEngine.Application.Commands.ApplyRule;

public class ApplyRuleCommand : IRequest<ApplyRuleResult>
{
    public string RuleCode { get; set; } = string.Empty;
    public string AwardCode { get; set; } = string.Empty;
}

public class ApplyRuleResult
{
    public string Status { get; set; } = string.Empty;
    public string ExecutionId { get; set; } = string.Empty;
    public string? ErrorMessage { get; set; }
}
