using MediatR;
using RuleEngine.Domain.Entities;
using System.ComponentModel.DataAnnotations;

namespace RuleEngine.Application.Commands.CreateRule;

public class CreateRuleCommand : IRequest<Rule>
{
    [Required(ErrorMessage = "Rule Code is required")]
    public string RuleCode { get; set; } = string.Empty;

    [Required(ErrorMessage = "Rule Name is required")]
    public string RuleName { get; set; } = string.Empty;

    [Required(ErrorMessage = "Rule Type is required")]
    public string RuleType { get; set; } = string.Empty;

    [Required(ErrorMessage = "Rule Category is required")]
    public string RuleCategory { get; set; } = string.Empty;

    [Range(0, 1000, ErrorMessage = "Priority must be between 0 and 1000")]
    public int Priority { get; set; }

    public bool IsActive { get; set; }

    [Required(ErrorMessage = "Created By is required")]
    public string CreatedBy { get; set; } = string.Empty;

    [Required(ErrorMessage = "Rule Expression is required")]
    public string RuleExpression { get; set; } = string.Empty;

    [Required(ErrorMessage = "Rule Definition is required")]
    public string RuleDefinition { get; set; } = string.Empty;

    public string? ApplicableFrom { get; set; }
    public string? ApplicableTo { get; set; }
}
