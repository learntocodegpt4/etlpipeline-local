using MediatR;
using RuleEngine.Application.Interfaces;
using RuleEngine.Domain.Entities;

namespace RuleEngine.Application.Queries.GetAwardsDetailed;

public class GetAwardsDetailedQueryHandler : IRequestHandler<GetAwardsDetailedQuery, IEnumerable<AwardDetailed>>
{
    private readonly IRuleEngineRepository _repository;

    public GetAwardsDetailedQueryHandler(IRuleEngineRepository repository)
    {
        _repository = repository;
    }

    public async Task<IEnumerable<AwardDetailed>> Handle(GetAwardsDetailedQuery request, CancellationToken cancellationToken)
    {
        return await _repository.GetAwardsDetailedAsync(request.AwardCode, request.RecordType, request.ClassificationFixedId);
    }
}
