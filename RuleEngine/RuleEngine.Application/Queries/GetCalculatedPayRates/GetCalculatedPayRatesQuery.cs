using MediatR;
using RuleEngine.Domain.Entities;
using System.Collections.Generic;

namespace RuleEngine.Application.Queries.GetCalculatedPayRates
{
    /// <summary>
    /// Query to get calculated pay rates with optional filtering
    /// </summary>
    public class GetCalculatedPayRatesQuery : IRequest<IEnumerable<CalculatedPayRate>>
    {
        public string AwardCode { get; set; }
        public int? ClassificationFixedId { get; set; }
        public string EmploymentType { get; set; }
        public string DayType { get; set; }
        public string ShiftType { get; set; }
        public string EmployeeAgeCategory { get; set; }
        public int PageNumber { get; set; } = 1;
        public int PageSize { get; set; } = 100;
    }
}
