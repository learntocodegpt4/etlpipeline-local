using MediatR;
using RuleEngine.Application.Interfaces;

namespace RuleEngine.Application.Commands.ApplyRule;

public class ApplyRuleCommandHandler : IRequestHandler<ApplyRuleCommand, ApplyRuleResult>
{
    private readonly IRuleEngineRepository _repository;

    public ApplyRuleCommandHandler(IRuleEngineRepository repository)
    {
        _repository = repository;
    }

    public async Task<ApplyRuleResult> Handle(ApplyRuleCommand request, CancellationToken cancellationToken)
    {
        return await _repository.ApplyRuleToAwardAsync(request.RuleCode, request.AwardCode);
    }
}
