using MediatR;
using Microsoft.AspNetCore.Mvc;
using RuleEngine.Application.Queries.GetRules;
using RuleEngine.Application.Commands.CreateRule;
using RuleEngine.Domain.Entities;

namespace RuleEngine.API.Controllers;

[ApiController]
[Route("api/[controller]")]
public class RulesController : ControllerBase
{
    private readonly IMediator _mediator;

    public RulesController(IMediator mediator)
    {
        _mediator = mediator;
    }

    /// <summary>
    /// Get all rules or filter by type and category
    /// </summary>
    [HttpGet]
    public async Task<IActionResult> GetRules([FromQuery] string? ruleType, [FromQuery] string? ruleCategory, [FromQuery] bool? isActive)
    {
        var query = new GetRulesQuery
        {
            RuleType = ruleType,
            RuleCategory = ruleCategory,
            IsActive = isActive
        };

        var result = await _mediator.Send(query);
        return Ok(result);
    }

    /// <summary>
    /// Create a new custom rule
    /// </summary>
    [HttpPost("create")]
    public async Task<IActionResult> CreateRule([FromBody] CreateRuleCommand command)
    {
        if (!ModelState.IsValid)
        {
            return BadRequest(new { message = "Validation failed", errors = ModelState.Values.SelectMany(v => v.Errors.Select(e => e.ErrorMessage)) });
        }

        try
        {
            var result = await _mediator.Send(command);
            return CreatedAtAction(nameof(GetRules), new { ruleCode = result.RuleCode }, result);
        }
        catch (InvalidOperationException ex)
        {
            return BadRequest(new { message = ex.Message });
        }
        catch (Exception ex)
        {
            return StatusCode(500, new { message = "An error occurred while creating the rule", details = ex.Message });
        }
    }
}
