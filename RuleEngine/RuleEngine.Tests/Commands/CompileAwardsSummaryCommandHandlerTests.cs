using FluentAssertions;
using Moq;
using RuleEngine.Application.Commands.CompileAwardsSummary;
using RuleEngine.Application.Interfaces;

namespace RuleEngine.Tests.Commands;

public class CompileAwardsSummaryCommandHandlerTests
{
    private readonly Mock<IRuleEngineRepository> _mockRepository;
    private readonly CompileAwardsSummaryCommandHandler _handler;

    public CompileAwardsSummaryCommandHandlerTests()
    {
        _mockRepository = new Mock<IRuleEngineRepository>();
        _handler = new CompileAwardsSummaryCommandHandler(_mockRepository.Object);
    }

    [Fact]
    public async Task Handle_ShouldReturnSuccess_WhenCompilationSucceeds()
    {
        // Arrange
        var command = new CompileAwardsSummaryCommand { AwardCode = "MA000001" };
        var expectedResult = new CompileAwardsSummaryResult
        {
            Status = "Success",
            RecordsCompiled = 10
        };

        _mockRepository
            .Setup(x => x.CompileAwardsSummaryAsync(command.AwardCode))
            .ReturnsAsync(expectedResult);

        // Act
        var result = await _handler.Handle(command, CancellationToken.None);

        // Assert
        result.Should().NotBeNull();
        result.Status.Should().Be("Success");
        result.RecordsCompiled.Should().Be(10);
        _mockRepository.Verify(x => x.CompileAwardsSummaryAsync(command.AwardCode), Times.Once);
    }

    [Fact]
    public async Task Handle_ShouldCompileAllAwards_WhenAwardCodeIsNull()
    {
        // Arrange
        var command = new CompileAwardsSummaryCommand { AwardCode = null };
        var expectedResult = new CompileAwardsSummaryResult
        {
            Status = "Success",
            RecordsCompiled = 100
        };

        _mockRepository
            .Setup(x => x.CompileAwardsSummaryAsync(null))
            .ReturnsAsync(expectedResult);

        // Act
        var result = await _handler.Handle(command, CancellationToken.None);

        // Assert
        result.Should().NotBeNull();
        result.Status.Should().Be("Success");
        result.RecordsCompiled.Should().Be(100);
    }
}
