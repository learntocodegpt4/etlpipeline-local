using MediatR;
using RuleEngine.Application.Interfaces;
using RuleEngine.Domain.Entities;

namespace RuleEngine.Application.Queries.GetAwards;

public class GetAwardsQueryHandler : IRequestHandler<GetAwardsQuery, IEnumerable<Award>>
{
    private readonly IRuleEngineRepository _repository;

    public GetAwardsQueryHandler(IRuleEngineRepository repository)
    {
        _repository = repository;
    }

    public async Task<IEnumerable<Award>> Handle(GetAwardsQuery request, CancellationToken cancellationToken)
    {
        return await _repository.GetAwardsAsync(request.AwardCode, request.IndustryType, request.IsActive);
    }
}
