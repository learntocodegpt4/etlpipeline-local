namespace RuleEngine.Domain.Entities;

public class Penalty
{
    public int Id { get; set; }
    public int PenaltyFixedId { get; set; }
    public string AwardCode { get; set; } = string.Empty;
    public string? PenaltyDescription { get; set; }
    public decimal? Rate { get; set; }
    public decimal? PenaltyCalculatedValue { get; set; }
    public int? ClassificationLevel { get; set; }
    public string? ClauseFixedId { get; set; }
    public string? ClauseDescription { get; set; }
    public string? BasePayRateId { get; set; }
    public DateTime? OperativeFrom { get; set; }
    public DateTime? OperativeTo { get; set; }
    public int? VersionNumber { get; set; }
    public int? PublishedYear { get; set; }
    public string? PenaltyType { get; set; }
    public string? ApplicableDay { get; set; }
    public DateTime CreatedAt { get; set; }
    public DateTime UpdatedAt { get; set; }
}
