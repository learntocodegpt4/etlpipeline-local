using System;

namespace RuleEngine.Domain.Entities
{
    /// <summary>
    /// Represents a calculated pay rate with all applied penalties, loadings, and conditions
    /// This is the master entity for displaying all possible pay scenarios to System Admin
    /// </summary>
    public class CalculatedPayRate
    {
        public long Id { get; set; }
        
        // Award and classification linkage
        public string AwardCode { get; set; }
        public string AwardName { get; set; }
        public int? ClassificationFixedId { get; set; }
        public string ClassificationName { get; set; }
        public int? ClassificationLevel { get; set; }
        
        // Base rate information
        public string BasePayRateId { get; set; }
        public decimal BaseRate { get; set; }
        public string BaseRateType { get; set; }
        
        // Employee attributes
        public string EmploymentType { get; set; }
        public string EmployeeAgeCategory { get; set; }
        public string EmployeeCategory { get; set; }
        
        // Scenario details
        public string DayType { get; set; }
        public string ShiftType { get; set; }
        public string TimeRange { get; set; }
        
        // Calculation breakdown
        public decimal? CasualLoadingApplied { get; set; }
        public decimal? CasualLoadedRate { get; set; }
        
        public decimal? JuniorPercentageApplied { get; set; }
        public decimal? JuniorAdjustedRate { get; set; }
        
        public decimal? ApprenticePercentageApplied { get; set; }
        public decimal? ApprenticeAdjustedRate { get; set; }
        
        public string PenaltyType { get; set; }
        public decimal? PenaltyMultiplierApplied { get; set; }
        public decimal? PenaltyFlatAmountApplied { get; set; }
        
        // Final calculated rate
        public decimal CalculatedHourlyRate { get; set; }
        public string CalculatedRateDescription { get; set; }
        
        // Calculation formula for audit
        public string CalculationSteps { get; set; }
        
        // Applicable allowances
        public string ApplicableAllowanceIds { get; set; }
        public decimal? ApplicableAllowanceTotal { get; set; }
        
        // Effective dates
        public DateTime EffectiveFrom { get; set; }
        public DateTime? EffectiveTo { get; set; }
        
        // FWC clause references
        public string PenaltyClauseReference { get; set; }
        public string CasualClauseReference { get; set; }
        public string JuniorClauseReference { get; set; }
        
        // Metadata
        public bool IsActive { get; set; }
        public DateTime CompiledAt { get; set; }
        public string CompiledBy { get; set; }
        public DateTime CreatedAt { get; set; }
        public DateTime UpdatedAt { get; set; }
    }
}
