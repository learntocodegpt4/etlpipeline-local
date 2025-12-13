using MediatR;

namespace RuleEngine.Application.Commands.CompileAwardsSummary;

public class CompileAwardsSummaryCommand : IRequest<CompileAwardsSummaryResult>
{
    public string? AwardCode { get; set; }
}

public class CompileAwardsSummaryResult
{
    public string Status { get; set; } = string.Empty;
    public int RecordsCompiled { get; set; }
    public string? ErrorMessage { get; set; }
}
