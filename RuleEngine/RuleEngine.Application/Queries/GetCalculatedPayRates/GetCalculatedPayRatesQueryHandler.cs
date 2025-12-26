using MediatR;
using RuleEngine.Application.Interfaces;
using RuleEngine.Domain.Entities;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;

namespace RuleEngine.Application.Queries.GetCalculatedPayRates
{
    public class GetCalculatedPayRatesQueryHandler : IRequestHandler<GetCalculatedPayRatesQuery, IEnumerable<CalculatedPayRate>>
    {
        private readonly IRuleEngineRepository _repository;

        public GetCalculatedPayRatesQueryHandler(IRuleEngineRepository repository)
        {
            _repository = repository;
        }

        public async Task<IEnumerable<CalculatedPayRate>> Handle(GetCalculatedPayRatesQuery request, CancellationToken cancellationToken)
        {
            return await _repository.GetCalculatedPayRatesAsync(
                request.AwardCode,
                request.ClassificationFixedId,
                request.EmploymentType,
                request.DayType,
                request.ShiftType,
                request.EmployeeAgeCategory,
                request.PageNumber,
                request.PageSize
            );
        }
    }
}
