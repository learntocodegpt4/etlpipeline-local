using MediatR;
using RuleEngine.Domain.Entities;

namespace RuleEngine.Application.Queries.GetAwardsDetailed;

public class GetAwardsDetailedQuery : IRequest<IEnumerable<AwardDetailed>>
{
    public string? AwardCode { get; set; }
    public string? RecordType { get; set; }
    public int? ClassificationFixedId { get; set; }
}
