using MediatR;
using RuleEngine.Application.Interfaces;

namespace RuleEngine.Application.Queries.GetPenalties;

public class GetPenaltiesQueryHandler : IRequestHandler<GetPenaltiesQuery, GetPenaltiesQueryResult>
{
    private readonly IRuleEngineRepository _repository;

    public GetPenaltiesQueryHandler(IRuleEngineRepository repository)
    {
        _repository = repository;
    }

    public async Task<GetPenaltiesQueryResult> Handle(GetPenaltiesQuery request, CancellationToken cancellationToken)
    {
        var (penalties, totalCount) = await _repository.GetPenaltiesAsync(
            request.AwardCode,
            request.ClassificationLevel,
            request.PenaltyType,
            request.Page,
            request.PageSize);

        return new GetPenaltiesQueryResult
        {
            Penalties = penalties,
            TotalCount = totalCount,
            Page = request.Page,
            PageSize = request.PageSize
        };
    }
}
