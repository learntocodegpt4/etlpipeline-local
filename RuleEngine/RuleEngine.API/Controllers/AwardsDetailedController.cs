using MediatR;
using Microsoft.AspNetCore.Mvc;
using RuleEngine.Application.Queries.GetAwardsDetailed;

namespace RuleEngine.API.Controllers;

[ApiController]
[Route("api/[controller]")]
public class AwardsDetailedController : ControllerBase
{
    private readonly IMediator _mediator;

    public AwardsDetailedController(IMediator mediator)
    {
        _mediator = mediator;
    }

    /// <summary>
    /// Get detailed award information with all combinations from staging tables
    /// This provides comprehensive data for System Admin UI display and tenant assignment
    /// </summary>
    [HttpGet]
    public async Task<IActionResult> GetAwardsDetailed(
        [FromQuery] string? awardCode, 
        [FromQuery] string? recordType, 
        [FromQuery] int? classificationFixedId)
    {
        var query = new GetAwardsDetailedQuery
        {
            AwardCode = awardCode,
            RecordType = recordType,
            ClassificationFixedId = classificationFixedId
        };

        var result = await _mediator.Send(query);
        return Ok(result);
    }
}
