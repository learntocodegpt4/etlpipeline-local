using MediatR;
using Microsoft.AspNetCore.Mvc;
using RuleEngine.Application.Queries.GetRules;

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
}
