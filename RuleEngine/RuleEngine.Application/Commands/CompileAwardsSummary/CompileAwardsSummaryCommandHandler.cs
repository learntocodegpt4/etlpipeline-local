using MediatR;
using RuleEngine.Application.Interfaces;

namespace RuleEngine.Application.Commands.CompileAwardsSummary;

public class CompileAwardsSummaryCommandHandler : IRequestHandler<CompileAwardsSummaryCommand, CompileAwardsSummaryResult>
{
    private readonly IRuleEngineRepository _repository;

    public CompileAwardsSummaryCommandHandler(IRuleEngineRepository repository)
    {
        _repository = repository;
    }

    public async Task<CompileAwardsSummaryResult> Handle(CompileAwardsSummaryCommand request, CancellationToken cancellationToken)
    {
        return await _repository.CompileAwardsSummaryAsync(request.AwardCode);
    }
}
