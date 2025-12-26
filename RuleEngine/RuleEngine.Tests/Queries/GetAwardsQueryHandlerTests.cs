using FluentAssertions;
using Moq;
using RuleEngine.Application.Interfaces;
using RuleEngine.Application.Queries.GetAwards;
using RuleEngine.Domain.Entities;

namespace RuleEngine.Tests.Queries;

public class GetAwardsQueryHandlerTests
{
    private readonly Mock<IRuleEngineRepository> _mockRepository;
    private readonly GetAwardsQueryHandler _handler;

    public GetAwardsQueryHandlerTests()
    {
        _mockRepository = new Mock<IRuleEngineRepository>();
        _handler = new GetAwardsQueryHandler(_mockRepository.Object);
    }

    [Fact]
    public async Task Handle_ShouldReturnAllAwards_WhenNoFiltersApplied()
    {
        // Arrange
        var query = new GetAwardsQuery();
        var expectedAwards = new List<Award>
        {
            new Award { AwardCode = "MA000001", AwardName = "Test Award 1" },
            new Award { AwardCode = "MA000002", AwardName = "Test Award 2" }
        };

        _mockRepository
            .Setup(x => x.GetAwardsAsync(null, null, null))
            .ReturnsAsync(expectedAwards);

        // Act
        var result = await _handler.Handle(query, CancellationToken.None);

        // Assert
        result.Should().NotBeNull();
        result.Should().HaveCount(2);
        result.Should().Contain(a => a.AwardCode == "MA000001");
    }

    [Fact]
    public async Task Handle_ShouldReturnFilteredAwards_WhenAwardCodeProvided()
    {
        // Arrange
        var query = new GetAwardsQuery { AwardCode = "MA000001" };
        var expectedAwards = new List<Award>
        {
            new Award { AwardCode = "MA000001", AwardName = "Test Award 1" }
        };

        _mockRepository
            .Setup(x => x.GetAwardsAsync("MA000001", null, null))
            .ReturnsAsync(expectedAwards);

        // Act
        var result = await _handler.Handle(query, CancellationToken.None);

        // Assert
        result.Should().NotBeNull();
        result.Should().HaveCount(1);
        result.First().AwardCode.Should().Be("MA000001");
    }
}
