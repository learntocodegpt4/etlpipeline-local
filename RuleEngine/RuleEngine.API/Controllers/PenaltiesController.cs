using MediatR;
using Microsoft.AspNetCore.Mvc;
using RuleEngine.Application.Queries.GetPenalties;

namespace RuleEngine.API.Controllers;

[ApiController]
[Route("api/[controller]")]
public class PenaltiesController : ControllerBase
{
    private readonly IMediator _mediator;
    private readonly ILogger<PenaltiesController> _logger;

    public PenaltiesController(IMediator mediator, ILogger<PenaltiesController> logger)
    {
        _mediator = mediator;
        _logger = logger;
    }

    /// <summary>
    /// Get penalties with optional filtering and pagination
    /// </summary>
    /// <param name="awardCode">Filter by award code (e.g., MA000120)</param>
    /// <param name="classificationLevel">Filter by classification level (1-4)</param>
    /// <param name="penaltyType">Filter by penalty type</param>
    /// <param name="page">Page number (default: 1)</param>
    /// <param name="pageSize">Page size (default: 100, max: 500)</param>
    /// <returns>Paginated list of penalties</returns>
    [HttpGet]
    [ProducesResponseType(typeof(GetPenaltiesQueryResult), 200)]
    [ProducesResponseType(400)]
    [ProducesResponseType(500)]
    public async Task<IActionResult> GetPenalties(
        [FromQuery] string? awardCode = null,
        [FromQuery] int? classificationLevel = null,
        [FromQuery] string? penaltyType = null,
        [FromQuery] int page = 1,
        [FromQuery] int pageSize = 100)
    {
        try
        {
            if (page < 1)
            {
                return BadRequest("Page must be greater than or equal to 1");
            }

            if (pageSize < 1 || pageSize > 500)
            {
                return BadRequest("Page size must be between 1 and 500");
            }

            var query = new GetPenaltiesQuery
            {
                AwardCode = awardCode,
                ClassificationLevel = classificationLevel,
                PenaltyType = penaltyType,
                Page = page,
                PageSize = pageSize
            };

            var result = await _mediator.Send(query);

            _logger.LogInformation(
                "Retrieved {Count} penalties (page {Page}/{TotalPages}) for award: {AwardCode}",
                result.Penalties.Count,
                result.Page,
                result.TotalPages,
                awardCode ?? "ALL");

            return Ok(result);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error retrieving penalties");
            return StatusCode(500, "An error occurred while retrieving penalties");
        }
    }

    /// <summary>
    /// Get penalty statistics for an award
    /// </summary>
    /// <param name="awardCode">Award code (required)</param>
    /// <returns>Penalty statistics</returns>
    [HttpGet("statistics")]
    [ProducesResponseType(200)]
    [ProducesResponseType(400)]
    public async Task<IActionResult> GetStatistics([FromQuery] string awardCode)
    {
        if (string.IsNullOrWhiteSpace(awardCode))
        {
            return BadRequest("Award code is required");
        }

        try
        {
            // Get all penalties for the award (first page only for statistics)
            var query = new GetPenaltiesQuery
            {
                AwardCode = awardCode,
                Page = 1,
                PageSize = 1  // We only need the count
            };

            var result = await _mediator.Send(query);

            var statistics = new
            {
                AwardCode = awardCode,
                TotalPenalties = result.TotalCount,
                TotalPages = result.TotalPages
            };

            return Ok(statistics);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error retrieving penalty statistics for award {AwardCode}", awardCode);
            return StatusCode(500, "An error occurred while retrieving penalty statistics");
        }
    }
}
