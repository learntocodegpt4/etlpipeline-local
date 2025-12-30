using MediatR;
using RuleEngine.Domain.Entities;

namespace RuleEngine.Application.Queries.GetAwards;

public class GetAwardsQuery : IRequest<IEnumerable<Award>>
{
    public string? AwardCode { get; set; }
    public string? IndustryType { get; set; }
    public bool? IsActive { get; set; }
}
