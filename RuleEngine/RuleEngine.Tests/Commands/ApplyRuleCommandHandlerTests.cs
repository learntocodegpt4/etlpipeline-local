using FluentAssertions;
using Moq;
using RuleEngine.Application.Commands.ApplyRule;
using RuleEngine.Application.Interfaces;

namespace RuleEngine.Tests.Commands;

public class ApplyRuleCommandHandlerTests
{
    private readonly Mock<IRuleEngineRepository> _mockRepository;
    private readonly ApplyRuleCommandHandler _handler;

    public ApplyRuleCommandHandlerTests()
    {
        _mockRepository = new Mock<IRuleEngineRepository>();
        _handler = new ApplyRuleCommandHandler(_mockRepository.Object);
    }

    [Fact]
    public async Task Handle_ShouldReturnSuccess_WhenRuleIsAppliedSuccessfully()
    {
        // Arrange
        var command = new ApplyRuleCommand
        {
            RuleCode = "RULE_MIN_PAY_RATE",
            AwardCode = "MA000001"
        };

        var expectedResult = new ApplyRuleResult
        {
            Status = "Success",
            ExecutionId = Guid.NewGuid().ToString()
        };

        _mockRepository
            .Setup(x => x.ApplyRuleToAwardAsync(command.RuleCode, command.AwardCode))
            .ReturnsAsync(expectedResult);

        // Act
        var result = await _handler.Handle(command, CancellationToken.None);

        // Assert
        result.Should().NotBeNull();
        result.Status.Should().Be("Success");
        result.ExecutionId.Should().NotBeNullOrEmpty();
        _mockRepository.Verify(x => x.ApplyRuleToAwardAsync(command.RuleCode, command.AwardCode), Times.Once);
    }

    [Fact]
    public async Task Handle_ShouldReturnError_WhenRuleApplicationFails()
    {
        // Arrange
        var command = new ApplyRuleCommand
        {
            RuleCode = "INVALID_RULE",
            AwardCode = "MA000001"
        };

        var expectedResult = new ApplyRuleResult
        {
            Status = "Error",
            ErrorMessage = "Rule not found"
        };

        _mockRepository
            .Setup(x => x.ApplyRuleToAwardAsync(command.RuleCode, command.AwardCode))
            .ReturnsAsync(expectedResult);

        // Act
        var result = await _handler.Handle(command, CancellationToken.None);

        // Assert
        result.Should().NotBeNull();
        result.Status.Should().Be("Error");
        result.ErrorMessage.Should().Be("Rule not found");
    }
}
