namespace RuleEngine.Domain.Entities;

public class CustomAward
{
    public int Id { get; set; }
    public string CustomAwardCode { get; set; } = string.Empty;
    public string BaseAwardCode { get; set; } = string.Empty;
    public string CustomAwardName { get; set; } = string.Empty;
    public string? TenantId { get; set; }
    public string? OrganizationId { get; set; }
    public decimal CustomPayRateMultiplier { get; set; } = 1.0m;
    public decimal? MinPayRateOverride { get; set; }
    public string? Customizations { get; set; }
    public bool IsActive { get; set; }
    public string CreatedBy { get; set; } = string.Empty;
    public DateTime CreatedAt { get; set; }
    public DateTime UpdatedAt { get; set; }
}
