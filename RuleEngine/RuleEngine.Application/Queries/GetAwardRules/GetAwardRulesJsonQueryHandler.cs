using MediatR;
using RuleEngine.Application.Interfaces;

namespace RuleEngine.Application.Queries.GetAwardRules;

public class GetAwardRulesJsonQueryHandler : IRequestHandler<GetAwardRulesJsonQuery, string>
{
    private readonly IRuleEngineRepository _repository;

    public GetAwardRulesJsonQueryHandler(IRuleEngineRepository repository)
    {
        _repository = repository;
    }

    public async Task<string> Handle(GetAwardRulesJsonQuery request, CancellationToken cancellationToken)
    {
        return await _repository.GenerateAwardRulesJsonAsync(request.AwardCode, request.RuleType);
    }
}
