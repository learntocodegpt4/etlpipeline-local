using MediatR;
using RuleEngine.Application.Interfaces;
using System.Threading;
using System.Threading.Tasks;

namespace RuleEngine.Application.Commands.CalculatePayRates
{
    public class CalculatePayRatesCommandHandler : IRequestHandler<CalculatePayRatesCommand, CalculatePayRatesResult>
    {
        private readonly IRuleEngineRepository _repository;

        public CalculatePayRatesCommandHandler(IRuleEngineRepository repository)
        {
            _repository = repository;
        }

        public async Task<CalculatePayRatesResult> Handle(CalculatePayRatesCommand request, CancellationToken cancellationToken)
        {
            return await _repository.CalculateAllPayRatesAsync(request.AwardCode, request.ClassificationFixedId);
        }
    }
}
