using MediatR;
using RuleEngine.Domain.Entities;

namespace RuleEngine.Application.Queries.GetRules;

public class GetRulesQuery : IRequest<IEnumerable<Rule>>
{
    public string? RuleType { get; set; }
    public string? RuleCategory { get; set; }
    public bool? IsActive { get; set; }
}
