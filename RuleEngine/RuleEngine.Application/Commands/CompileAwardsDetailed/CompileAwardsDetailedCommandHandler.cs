using MediatR;
using RuleEngine.Application.Interfaces;

namespace RuleEngine.Application.Commands.CompileAwardsDetailed;

public class CompileAwardsDetailedCommandHandler : IRequestHandler<CompileAwardsDetailedCommand, CompileAwardsDetailedResult>
{
    private readonly IRuleEngineRepository _repository;

    public CompileAwardsDetailedCommandHandler(IRuleEngineRepository repository)
    {
        _repository = repository;
    }

    public async Task<CompileAwardsDetailedResult> Handle(CompileAwardsDetailedCommand request, CancellationToken cancellationToken)
    {
        return await _repository.CompileAwardsDetailedAsync(request.AwardCode);
    }
}
