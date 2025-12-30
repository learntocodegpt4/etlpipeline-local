using MediatR;

namespace RuleEngine.Application.Commands.CalculatePayRates
{
    /// <summary>
    /// Command to calculate all possible pay rates for an award or all awards
    /// </summary>
    public class CalculatePayRatesCommand : IRequest<CalculatePayRatesResult>
    {
        public string AwardCode { get; set; }
        public int? ClassificationFixedId { get; set; }
    }

    public class CalculatePayRatesResult
    {
        public string Status { get; set; }
        public int TotalRecordsCreated { get; set; }
        public int DurationSeconds { get; set; }
        public int AwardsProcessed { get; set; }
        public int ClassificationsProcessed { get; set; }
        public int FullTimeRates { get; set; }
        public int PartTimeRates { get; set; }
        public int CasualRates { get; set; }
        public string Message { get; set; }
    }
}
