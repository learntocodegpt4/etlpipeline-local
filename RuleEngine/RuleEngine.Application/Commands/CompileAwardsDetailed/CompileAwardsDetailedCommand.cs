using MediatR;

namespace RuleEngine.Application.Commands.CompileAwardsDetailed;

public class CompileAwardsDetailedCommand : IRequest<CompileAwardsDetailedResult>
{
    public string? AwardCode { get; set; }
}

public class CompileAwardsDetailedResult
{
    public string Status { get; set; } = string.Empty;
    public int TotalRecords { get; set; }
    public int TotalAwards { get; set; }
    public int BaseRecords { get; set; }
    public int ClassificationRecords { get; set; }
    public int PayRateRecords { get; set; }
    public int ExpenseRecords { get; set; }
    public int WageRecords { get; set; }
    public string? ErrorMessage { get; set; }
}
