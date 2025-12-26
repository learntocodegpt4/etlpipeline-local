# SQL Stored Procedures Documentation

This document describes the stored procedures created for the Rule Engine system.

## Overview

The stored procedures provide the data layer for awards compilation, rule management, and rule execution. They analyze data from the ETL pipeline staging tables and maintain the rules engine tables.

## Stored Procedures

### 1. sp_CompileAwardsSummary

Compiles awards summary data from staging tables.

#### Purpose
Analyzes all staging tables (awards, classifications, pay rates, allowances) and generates aggregated summary data for each award.

#### Parameters
- `@award_code` (NVARCHAR(50), optional): Specific award code to compile. If NULL, compiles all awards.

#### Returns
- `Status`: "Success" or "Error"
- `RecordsCompiled`: Number of records compiled
- `ErrorMessage`: Error details if failed

#### Usage

Compile all awards:
```sql
EXEC sp_CompileAwardsSummary;
```

Compile specific award:
```sql
EXEC sp_CompileAwardsSummary @award_code = 'MA000001';
```

#### Processing Logic

1. Queries staging tables:
   - `Stg_TblAwards` - Base award data
   - `Stg_TblClassifications` - Classification counts
   - `Stg_TblPayRates` - Pay rate statistics
   - `Stg_TblExpenseAllowances` - Expense allowance counts
   - `Stg_TblWageAllowances` - Wage allowance counts

2. Calculates:
   - Total counts for each data type
   - Minimum, maximum, and average base rates
   - Compilation timestamp

3. Stores results in `TblAwardsSummary`

#### Performance
- Uses indexed queries on award_code
- Leverages aggregation functions
- Transaction-safe operation

---

### 2. sp_InitializeBasicRules

Initializes the default set of rules for the system.

#### Purpose
Creates 12 predefined rules (6 simple, 6 complex) for award management and compliance.

#### Parameters
None

#### Returns
- `Status`: "Success" or "Error"
- `RulesInitialized`: Number of rules created
- `ErrorMessage`: Error details if failed

#### Usage
```sql
EXEC sp_InitializeBasicRules;
```

#### Rules Created

**Simple Rules:**
1. `RULE_MIN_PAY_RATE` - Minimum Pay Rate Validation (Priority: 100)
2. `RULE_PAY_RANGE` - Pay Rate Range Validation (Priority: 90)
3. `RULE_CLASS_LEVEL` - Classification Level Hierarchy (Priority: 80)
4. `RULE_ALLOWANCE_RATE` - Allowance Rate Validation (Priority: 70)
5. `RULE_OPERATIVE_DATES` - Award Operative Date Validation (Priority: 60)
6. `RULE_ALL_PURPOSE` - All-Purpose Allowance Classification (Priority: 50)

**Complex Rules:**
1. `RULE_PAY_PROGRESSION` - Pay Rate Progression Validation (Priority: 100)
2. `RULE_CUSTOM_PAY_OVERRIDE` - Custom Award Pay Rate Override (Priority: 95)
3. `RULE_TOTAL_ALLOWANCES` - Total Allowances Calculation (Priority: 85)
4. `RULE_VERSION_CONTROL` - Award Version Control (Priority: 90)
5. `RULE_CLASS_HIERARCHY` - Classification Hierarchy Integrity (Priority: 80)
6. `RULE_INDUSTRY_ASSIGN` - Industry-Specific Award Assignment (Priority: 75)

#### Notes
- Rules are only created if they don't already exist (idempotent)
- Each rule has a unique rule_code
- Priority determines execution order (higher = first)
- All rules are created as active by default

---

### 3. sp_ApplyRuleToAward

Applies a specific rule to an award and logs the execution.

#### Purpose
Associates a rule with an award, marks it as applied, and creates an audit trail.

#### Parameters
- `@rule_code` (NVARCHAR(50), required): Code of the rule to apply
- `@award_code` (NVARCHAR(50), required): Code of the target award

#### Returns
- `Status`: "Success" or "Error"
- `ExecutionId`: Unique GUID for this execution
- `ErrorMessage`: Error details if failed

#### Usage
```sql
EXEC sp_ApplyRuleToAward 
    @rule_code = 'RULE_MIN_PAY_RATE',
    @award_code = 'MA000001';
```

#### Processing Logic

1. Validates rule exists and is active
2. Validates award exists in summary table
3. Creates or updates record in `TblAwardRules`
4. Logs execution details in `TblRuleExecutionLog`
5. Measures and records execution duration

#### Error Handling
- Returns error if rule not found or inactive
- Returns error if award not found
- Logs all execution attempts (success or failure)

#### Audit Trail
Each execution creates a record with:
- Unique execution ID
- Rule and award codes
- Execution status (SUCCESS/FAILED/SKIPPED)
- Duration in milliseconds
- Timestamp

---

### 4. sp_GenerateAwardRulesJSON

Generates JSON output of rules and their award associations.

#### Purpose
Creates a JSON representation of rules and which awards they're applied to, useful for API responses and exports.

#### Parameters
- `@award_code` (NVARCHAR(50), optional): Filter by specific award
- `@rule_type` (NVARCHAR(50), optional): Filter by rule type (SIMPLE/COMPLEX)

#### Returns
- `rules_json`: JSON string containing rules and their associated awards

#### Usage

Get all rules:
```sql
EXEC sp_GenerateAwardRulesJSON;
```

Get simple rules only:
```sql
EXEC sp_GenerateAwardRulesJSON @rule_type = 'SIMPLE';
```

Get rules for specific award:
```sql
EXEC sp_GenerateAwardRulesJSON @award_code = 'MA000001';
```

Get complex rules for specific award:
```sql
EXEC sp_GenerateAwardRulesJSON 
    @award_code = 'MA000001',
    @rule_type = 'COMPLEX';
```

#### Output Format

```json
[
  {
    "rule_code": "RULE_MIN_PAY_RATE",
    "rule_name": "Minimum Pay Rate Validation",
    "rule_type": "SIMPLE",
    "rule_category": "PAY_RATE",
    "rule_definition": "Validates that all pay rates meet or exceed FWC minimum standards",
    "rule_expression": "base_rate >= min_fwc_rate",
    "priority": 100,
    "is_active": true,
    "applied_awards": [
      {
        "award_code": "MA000001",
        "award_name": "Fast Food Industry Award 2020",
        "is_applied": true,
        "applied_at": "2024-12-13T10:30:00",
        "result_summary": "Rule applied successfully"
      }
    ]
  }
]
```

#### Performance
- Uses JSON PATH for efficient JSON generation
- Nested query for award associations
- Filtered by active rules only

---

## Database Tables Used

### Input Tables (Staging)
- `Stg_TblAwards`
- `Stg_TblClassifications`
- `Stg_TblPayRates`
- `Stg_TblExpenseAllowances`
- `Stg_TblWageAllowances`

### Output Tables (Rules Engine)
- `TblAwardsSummary` - Compiled award statistics
- `TblRules` - Rule definitions
- `TblAwardRules` - Award-rule associations
- `TblRuleExecutionLog` - Execution audit trail
- `TblCustomAwards` - Custom award definitions

---

## Common Usage Patterns

### Initial Setup
```sql
-- 1. Initialize rules
EXEC sp_InitializeBasicRules;

-- 2. Compile all awards
EXEC sp_CompileAwardsSummary;

-- 3. Verify compilation
SELECT * FROM TblAwardsSummary;
```

### Apply Rules to All Awards
```sql
DECLARE @award_code NVARCHAR(50);
DECLARE @rule_code NVARCHAR(50) = 'RULE_MIN_PAY_RATE';

DECLARE award_cursor CURSOR FOR 
    SELECT award_code FROM TblAwardsSummary WHERE is_active = 1;

OPEN award_cursor;
FETCH NEXT FROM award_cursor INTO @award_code;

WHILE @@FETCH_STATUS = 0
BEGIN
    EXEC sp_ApplyRuleToAward 
        @rule_code = @rule_code,
        @award_code = @award_code;
        
    FETCH NEXT FROM award_cursor INTO @award_code;
END

CLOSE award_cursor;
DEALLOCATE award_cursor;
```

### Re-compile After ETL Update
```sql
-- After ETL pipeline updates staging tables
EXEC sp_CompileAwardsSummary;

-- Verify updates
SELECT 
    award_code,
    award_name,
    total_pay_rates,
    compiled_at
FROM TblAwardsSummary
ORDER BY compiled_at DESC;
```

### Generate Rules Report
```sql
-- Get all rules with their applications
EXEC sp_GenerateAwardRulesJSON;

-- Get only complex rules
EXEC sp_GenerateAwardRulesJSON @rule_type = 'COMPLEX';

-- Get rules for specific award
EXEC sp_GenerateAwardRulesJSON @award_code = 'MA000001';
```

---

## Error Handling

All stored procedures include TRY-CATCH blocks for error handling:

```sql
BEGIN TRY
    -- Processing logic
    SELECT 'Success' as Status, @@ROWCOUNT as RecordsCompiled;
END TRY
BEGIN CATCH
    SELECT 'Error' as Status, ERROR_MESSAGE() as ErrorMessage;
END CATCH
```

---

## Monitoring and Maintenance

### Check Rule Execution History
```sql
SELECT 
    execution_id,
    rule_code,
    award_code,
    execution_status,
    execution_duration_ms,
    executed_at
FROM TblRuleExecutionLog
ORDER BY executed_at DESC;
```

### Performance Monitoring
```sql
-- Average execution time by rule
SELECT 
    rule_code,
    COUNT(*) as execution_count,
    AVG(execution_duration_ms) as avg_duration_ms,
    MAX(execution_duration_ms) as max_duration_ms
FROM TblRuleExecutionLog
WHERE execution_status = 'SUCCESS'
GROUP BY rule_code
ORDER BY avg_duration_ms DESC;
```

### Check Compilation Status
```sql
SELECT 
    COUNT(*) as total_awards,
    SUM(CASE WHEN compiled_at >= DATEADD(hour, -24, GETUTCDATE()) THEN 1 ELSE 0 END) as compiled_last_24h,
    MAX(compiled_at) as last_compilation
FROM TblAwardsSummary;
```

---

## Best Practices

1. **Regular Compilation**: Run `sp_CompileAwardsSummary` after each ETL pipeline execution
2. **Rule Initialization**: Run `sp_InitializeBasicRules` only once during setup
3. **Error Checking**: Always check the Status field in return values
4. **Logging**: Monitor `TblRuleExecutionLog` for execution patterns and errors
5. **Performance**: Use indexes on award_code, rule_code, and date fields
6. **Transactions**: Consider wrapping multiple calls in transactions for consistency

---

## Troubleshooting

### Issue: Compilation returns 0 records
**Solution**: Verify staging tables contain data
```sql
SELECT COUNT(*) FROM Stg_TblAwards;
SELECT COUNT(*) FROM Stg_TblPayRates;
```

### Issue: Rule application fails
**Solution**: Check if rule and award exist
```sql
SELECT * FROM TblRules WHERE rule_code = 'YOUR_RULE_CODE';
SELECT * FROM TblAwardsSummary WHERE award_code = 'YOUR_AWARD_CODE';
```

### Issue: Slow performance
**Solution**: Verify indexes exist
```sql
SELECT * FROM sys.indexes 
WHERE object_id IN (
    OBJECT_ID('TblAwardsSummary'),
    OBJECT_ID('TblRules'),
    OBJECT_ID('TblAwardRules')
);
```
