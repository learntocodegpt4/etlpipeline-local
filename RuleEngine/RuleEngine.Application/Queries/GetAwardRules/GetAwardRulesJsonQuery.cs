using MediatR;

namespace RuleEngine.Application.Queries.GetAwardRules;

public class GetAwardRulesJsonQuery : IRequest<string>
{
    public string? AwardCode { get; set; }
    public string? RuleType { get; set; }
}
