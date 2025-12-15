using MediatR;
using Microsoft.AspNetCore.Mvc;
using RuleEngine.Application.Commands.ApplyRule;
using RuleEngine.Application.Commands.CompileAwardsSummary;
using RuleEngine.Application.Commands.CompileAwardsDetailed;
using RuleEngine.Application.Queries.GetAwardRules;

namespace RuleEngine.API.Controllers;

[ApiController]
[Route("api/[controller]")]
public class RuleEngineController : ControllerBase
{
    private readonly IMediator _mediator;

    public RuleEngineController(IMediator mediator)
    {
        _mediator = mediator;
    }

    /// <summary>
    /// Compile awards summary from staging tables
    /// </summary>
    [HttpPost("compile-awards")]
    public async Task<IActionResult> CompileAwardsSummary([FromBody] CompileAwardsSummaryCommand command)
    {
        var result = await _mediator.Send(command);
        return Ok(result);
    }

    /// <summary>
    /// Compile comprehensive award details with all combinations from staging tables
    /// This provides maximum information for System Admin UI display
    /// </summary>
    [HttpPost("compile-awards-detailed")]
    public async Task<IActionResult> CompileAwardsDetailed([FromBody] CompileAwardsDetailedCommand command)
    {
        var result = await _mediator.Send(command);
        return Ok(result);
    }

    /// <summary>
    /// Apply a specific rule to an award
    /// </summary>
    [HttpPost("apply-rule")]
    public async Task<IActionResult> ApplyRule([FromBody] ApplyRuleCommand command)
    {
        var result = await _mediator.Send(command);
        return Ok(result);
    }

    /// <summary>
    /// Generate JSON output of award rules
    /// </summary>
    [HttpGet("award-rules-json")]
    public async Task<IActionResult> GetAwardRulesJson([FromQuery] string? awardCode, [FromQuery] string? ruleType)
    {
        var query = new GetAwardRulesJsonQuery
        {
            AwardCode = awardCode,
            RuleType = ruleType
        };

        var result = await _mediator.Send(query);
        return Content(result, "application/json");
    }
}
