using MediatR;
using Microsoft.AspNetCore.Mvc;
using RuleEngine.Application.Queries.GetAwards;

namespace RuleEngine.API.Controllers;

[ApiController]
[Route("api/[controller]")]
public class AwardsController : ControllerBase
{
    private readonly IMediator _mediator;

    public AwardsController(IMediator mediator)
    {
        _mediator = mediator;
    }

    /// <summary>
    /// Get all awards or filter by specific criteria
    /// </summary>
    [HttpGet]
    public async Task<IActionResult> GetAwards([FromQuery] string? awardCode, [FromQuery] string? industryType, [FromQuery] bool? isActive)
    {
        var query = new GetAwardsQuery
        {
            AwardCode = awardCode,
            IndustryType = industryType,
            IsActive = isActive
        };

        var result = await _mediator.Send(query);
        return Ok(result);
    }
}
