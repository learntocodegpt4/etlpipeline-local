using MediatR;
using RuleEngine.Application.Interfaces;
using RuleEngine.Domain.Entities;

namespace RuleEngine.Application.Queries.GetRules;

public class GetRulesQueryHandler : IRequestHandler<GetRulesQuery, IEnumerable<Rule>>
{
    private readonly IRuleEngineRepository _repository;

    public GetRulesQueryHandler(IRuleEngineRepository repository)
    {
        _repository = repository;
    }

    public async Task<IEnumerable<Rule>> Handle(GetRulesQuery request, CancellationToken cancellationToken)
    {
        return await _repository.GetRulesAsync(request.RuleType, request.RuleCategory, request.IsActive);
    }
}
