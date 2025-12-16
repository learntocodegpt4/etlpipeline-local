using MediatR;
using RuleEngine.Domain.Entities;

namespace RuleEngine.Application.Queries.GetPenalties;

public class GetPenaltiesQuery : IRequest<GetPenaltiesQueryResult>
{
    public string? AwardCode { get; set; }
    public int? ClassificationLevel { get; set; }
    public string? PenaltyType { get; set; }
    public int Page { get; set; } = 1;
    public int PageSize { get; set; } = 100;
}

public class GetPenaltiesQueryResult
{
    public List<Penalty> Penalties { get; set; } = new();
    public int TotalCount { get; set; }
    public int Page { get; set; }
    public int PageSize { get; set; }
    public int TotalPages => (int)Math.Ceiling((double)TotalCount / PageSize);
}
