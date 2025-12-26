# Rule Engine Microservice

A .NET-based Rule Engine microservice for managing and processing awards, pay conditions, and compliance rules for the RosteredAI workforce management system.

## Overview

This microservice is built using Clean Architecture principles with CQRS pattern implementation using MediatR. It provides a scalable and performant solution for:

- Compiling awards summaries from staging tables
- Managing simple and complex rules for payroll automation
- Applying rules to awards with execution tracking
- Generating JSON outputs for awards and rules
- Supporting custom award creation with FWC compliance

## Architecture

The solution follows Clean Architecture with clear separation of concerns:

```
RuleEngine/
├── RuleEngine.Domain/          # Domain entities and enums
├── RuleEngine.Application/     # CQRS Commands, Queries, and Interfaces
├── RuleEngine.Infrastructure/  # Data access and repository implementations
├── RuleEngine.API/             # REST API controllers and configuration
└── RuleEngine.Tests/           # Unit tests
```

### Design Patterns

- **CQRS (Command Query Responsibility Segregation)**: Using MediatR for separating read and write operations
- **Repository Pattern**: Data access abstraction
- **Dependency Injection**: For loose coupling and testability
- **Clean Architecture**: Domain-centric design with dependency inversion

## Prerequisites

- .NET 10 SDK
- MS SQL Server (with etl_pipeline database)
- Connection to the same database used by the Python ETL pipeline

## Database Setup

Run the following SQL migrations in order:

1. `migrations/sql/004_create_rules_tables.sql` - Creates rules engine tables
2. `migrations/sql/005_create_stored_procedures.sql` - Creates stored procedures

### Key Database Tables

- **TblAwardsSummary**: Compiled awards data with statistics
- **TblRules**: Simple and complex rules definitions
- **TblAwardRules**: Mapping of rules to awards
- **TblCustomAwards**: Custom awards for tenants/organizations
- **TblRuleExecutionLog**: Audit trail of rule executions

### Stored Procedures

- **sp_CompileAwardsSummary**: Analyzes staging tables and generates awards summary
- **sp_InitializeBasicRules**: Initializes the default set of simple and complex rules
- **sp_ApplyRuleToAward**: Applies a specific rule to an award
- **sp_GenerateAwardRulesJSON**: Generates JSON output of award rules

## Configuration

Update `appsettings.json` with your database connection string:

```json
{
  "DatabaseSettings": {
    "ConnectionString": "Server=localhost;Database=etl_pipeline;User Id=sa;Password=YourPassword;TrustServerCertificate=True;"
  }
}
```

## Running the Application

### Development

```bash
cd RuleEngine
dotnet run --project RuleEngine.API
```

The API will be available at:
- HTTP: `http://localhost:5000`
- HTTPS: `https://localhost:5001`
- Swagger UI: `http://localhost:5000/swagger`

### Build

```bash
cd RuleEngine
dotnet build
```

### Run Tests

```bash
cd RuleEngine
dotnet test
```

## API Endpoints

### Awards

#### GET /api/awards
Get all awards or filter by specific criteria.

**Query Parameters:**
- `awardCode` (optional): Filter by award code
- `industryType` (optional): Filter by industry type
- `isActive` (optional): Filter by active status

**Example:**
```bash
curl -X GET "http://localhost:5000/api/awards?isActive=true"
```

### Rules

#### GET /api/rules
Get all rules or filter by type and category.

**Query Parameters:**
- `ruleType` (optional): SIMPLE or COMPLEX
- `ruleCategory` (optional): PAY_RATE, ALLOWANCE, CLASSIFICATION, COMPLIANCE
- `isActive` (optional): Filter by active status

**Example:**
```bash
curl -X GET "http://localhost:5000/api/rules?ruleType=SIMPLE&isActive=true"
```

### Rule Engine Operations

#### POST /api/ruleengine/compile-awards
Compile awards summary from staging tables.

**Request Body:**
```json
{
  "awardCode": "MA000001"  // Optional - omit to compile all awards
}
```

**Response:**
```json
{
  "status": "Success",
  "recordsCompiled": 10,
  "errorMessage": null
}
```

**Example:**
```bash
curl -X POST "http://localhost:5000/api/ruleengine/compile-awards" \
  -H "Content-Type: application/json" \
  -d '{"awardCode": "MA000001"}'
```

#### POST /api/ruleengine/apply-rule
Apply a specific rule to an award.

**Request Body:**
```json
{
  "ruleCode": "RULE_MIN_PAY_RATE",
  "awardCode": "MA000001"
}
```

**Response:**
```json
{
  "status": "Success",
  "executionId": "guid-here",
  "errorMessage": null
}
```

**Example:**
```bash
curl -X POST "http://localhost:5000/api/ruleengine/apply-rule" \
  -H "Content-Type: application/json" \
  -d '{"ruleCode": "RULE_MIN_PAY_RATE", "awardCode": "MA000001"}'
```

#### GET /api/ruleengine/award-rules-json
Generate JSON output of award rules.

**Query Parameters:**
- `awardCode` (optional): Filter by award code
- `ruleType` (optional): SIMPLE or COMPLEX

**Example:**
```bash
curl -X GET "http://localhost:5000/api/ruleengine/award-rules-json?ruleType=SIMPLE"
```

## Rule Types

### Simple Rules

1. **RULE_MIN_PAY_RATE**: Minimum Pay Rate Validation
2. **RULE_PAY_RANGE**: Pay Rate Range Validation
3. **RULE_CLASS_LEVEL**: Classification Level Hierarchy
4. **RULE_ALLOWANCE_RATE**: Allowance Rate Validation
5. **RULE_OPERATIVE_DATES**: Award Operative Date Validation
6. **RULE_ALL_PURPOSE**: All-Purpose Allowance Classification

### Complex Rules

1. **RULE_PAY_PROGRESSION**: Pay Rate Progression Validation
2. **RULE_CUSTOM_PAY_OVERRIDE**: Custom Award Pay Rate Override
3. **RULE_TOTAL_ALLOWANCES**: Total Allowances Calculation
4. **RULE_VERSION_CONTROL**: Award Version Control
5. **RULE_CLASS_HIERARCHY**: Classification Hierarchy Integrity
6. **RULE_INDUSTRY_ASSIGN**: Industry-Specific Award Assignment

## Initialization

After setting up the database and running migrations, initialize the basic rules:

```sql
EXEC sp_InitializeBasicRules;
```

Then compile awards summaries:

```sql
EXEC sp_CompileAwardsSummary;
```

Or use the API:

```bash
curl -X POST "http://localhost:5000/api/ruleengine/compile-awards" \
  -H "Content-Type: application/json" \
  -d '{}'
```

## Testing

The solution includes comprehensive unit tests using:
- **xUnit**: Test framework
- **Moq**: Mocking framework
- **FluentAssertions**: Assertion library

Run tests with:
```bash
dotnet test
```

Test coverage includes:
- Command handlers
- Query handlers
- Repository methods (mocked)

## Performance Considerations

- **Dapper**: Used for high-performance database access
- **Stored Procedures**: Pre-compiled database operations
- **Async/Await**: Throughout for scalability
- **Indexes**: On all key database columns for fast queries
- **Connection Pooling**: Enabled by default in SqlConnection

## Security

- TrustServerCertificate should only be True in development
- Use integrated security or strong passwords in production
- Validate all inputs through MediatR pipeline behaviors
- Use parameterized queries to prevent SQL injection

## Integration with ETL Pipeline

This microservice connects to the same MS SQL database used by the Python ETL pipeline. It reads from the staging tables:

- `Stg_TblAwards`
- `Stg_TblClassifications`
- `Stg_TblPayRates`
- `Stg_TblExpenseAllowances`
- `Stg_TblWageAllowances`

And manages its own tables for rules and compiled data.

## Future Enhancements

- Add authentication and authorization
- Implement caching for frequently accessed data
- Add validation using FluentValidation
- Implement API versioning
- Add distributed logging and monitoring
- Implement event sourcing for audit trail
- Add GraphQL support

## License

MIT License - see LICENSE file for details.
