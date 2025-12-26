using MediatR;
using Microsoft.AspNetCore.Mvc;
using RuleEngine.Application.Commands.CalculatePayRates;
using RuleEngine.Application.Queries.GetCalculatedPayRates;

namespace RuleEngine.API.Controllers;

[ApiController]
[Route("api/[controller]")]
public class CalculatedPayRatesController : ControllerBase
{
    private readonly IMediator _mediator;

    public CalculatedPayRatesController(IMediator mediator)
    {
        _mediator = mediator;
    }

    /// <summary>
    /// Get calculated pay rates with optional filtering
    /// </summary>
    /// <param name="awardCode">Optional: Filter by award code (e.g., MA000120)</param>
    /// <param name="classificationFixedId">Optional: Filter by classification ID</param>
    /// <param name="employmentType">Optional: Filter by employment type (FULL_TIME, PART_TIME, CASUAL)</param>
    /// <param name="dayType">Optional: Filter by day type (WEEKDAY, SATURDAY, SUNDAY, PUBLIC_HOLIDAY)</param>
    /// <param name="shiftType">Optional: Filter by shift type (STANDARD, NIGHT, AFTERNOON, OVERTIME_FIRST2HR, etc.)</param>
    /// <param name="employeeAgeCategory">Optional: Filter by age category (ADULT, AGE_20, AGE_19, AGE_18, etc.)</param>
    /// <param name="pageNumber">Page number (default: 1)</param>
    /// <param name="pageSize">Page size (default: 100, max: 500)</param>
    [HttpGet]
    public async Task<IActionResult> GetCalculatedPayRates(
        [FromQuery] string? awardCode = null,
        [FromQuery] int? classificationFixedId = null,
        [FromQuery] string? employmentType = null,
        [FromQuery] string? dayType = null,
        [FromQuery] string? shiftType = null,
        [FromQuery] string? employeeAgeCategory = null,
        [FromQuery] int pageNumber = 1,
        [FromQuery] int pageSize = 100)
    {
        if (pageSize > 500)
        {
            return BadRequest("Page size cannot exceed 500");
        }

        var query = new GetCalculatedPayRatesQuery
        {
            AwardCode = awardCode,
            ClassificationFixedId = classificationFixedId,
            EmploymentType = employmentType,
            DayType = dayType,
            ShiftType = shiftType,
            EmployeeAgeCategory = employeeAgeCategory,
            PageNumber = pageNumber,
            PageSize = pageSize
        };

        var result = await _mediator.Send(query);
        return Ok(result);
    }

    /// <summary>
    /// Calculate all possible pay rates for an award or all awards
    /// </summary>
    /// <param name="command">Calculation parameters (optional award_code and classification_fixed_id)</param>
    /// <remarks>
    /// This endpoint triggers the stored procedure to calculate all possible pay rate combinations.
    /// 
    /// Calculations include:
    /// - All employment types (Full-time, Part-time, Casual)
    /// - All day types (Weekday, Saturday, Sunday, Public Holiday)
    /// - All shift types (Standard, Night, Afternoon, Overtime)
    /// - All age categories (Adult, Junior)
    /// - All penalty scenarios and compound calculations
    /// 
    /// Examples:
    /// - Calculate for all awards: POST with empty body {}
    /// - Calculate for one award: POST with {"awardCode": "MA000120"}
    /// - Calculate for one classification: POST with {"awardCode": "MA000120", "classificationFixedId": 4591}
    /// 
    /// Warning: Calculating for all awards may take several minutes and generate thousands of records.
    /// </remarks>
    [HttpPost("calculate")]
    public async Task<IActionResult> CalculatePayRates([FromBody] CalculatePayRatesCommand command)
    {
        var result = await _mediator.Send(command);
        
        if (result.Status != "Success")
        {
            return StatusCode(500, result);
        }

        return Ok(result);
    }

    /// <summary>
    /// Get pay rate calculation summary statistics
    /// </summary>
    [HttpGet("statistics")]
    public async Task<IActionResult> GetStatistics([FromQuery] string? awardCode = null)
    {
        var query = new GetCalculatedPayRatesQuery
        {
            AwardCode = awardCode,
            PageNumber = 1,
            PageSize = 1
        };

        var allRates = await _mediator.Send(query);
        
        var stats = new
        {
            TotalRates = allRates.Count(),
            ByEmploymentType = allRates.GroupBy(r => r.EmploymentType)
                .Select(g => new { EmploymentType = g.Key, Count = g.Count() }),
            ByDayType = allRates.GroupBy(r => r.DayType)
                .Select(g => new { DayType = g.Key, Count = g.Count() }),
            ByShiftType = allRates.GroupBy(r => r.ShiftType)
                .Select(g => new { ShiftType = g.Key, Count = g.Count() }),
            AverageRate = allRates.Average(r => r.CalculatedHourlyRate),
            MinRate = allRates.Min(r => r.CalculatedHourlyRate),
            MaxRate = allRates.Max(r => r.CalculatedHourlyRate)
        };

        return Ok(stats);
    }
}
