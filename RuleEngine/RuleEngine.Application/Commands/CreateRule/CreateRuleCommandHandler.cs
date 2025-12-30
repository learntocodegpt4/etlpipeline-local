using MediatR;
using RuleEngine.Domain.Entities;
using RuleEngine.Application.Interfaces;

namespace RuleEngine.Application.Commands.CreateRule;

public class CreateRuleCommandHandler : IRequestHandler<CreateRuleCommand, Rule>
{
    private readonly IRuleEngineRepository _repository;

    public CreateRuleCommandHandler(IRuleEngineRepository repository)
    {
        _repository = repository;
    }

    public async Task<Rule> Handle(CreateRuleCommand request, CancellationToken cancellationToken)
    {
        var rule = new Rule
        {
            RuleCode = request.RuleCode,
            RuleName = request.RuleName,
            RuleType = request.RuleType,
            RuleCategory = request.RuleCategory,
            Priority = request.Priority,
            IsActive = request.IsActive,
            CreatedBy = request.CreatedBy,
            RuleExpression = request.RuleExpression,
            RuleDefinition = request.RuleDefinition,
            CreatedAt = DateTime.UtcNow,
            UpdatedAt = DateTime.UtcNow
        };

        try
        {
            return await _repository.CreateRuleAsync(rule);
        }
        catch (Exception ex)
        {
            throw new InvalidOperationException($"Failed to create rule: {ex.Message}", ex);
        }
    }
}
