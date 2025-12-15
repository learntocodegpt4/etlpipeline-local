# Awards Detailed Compilation - System Admin Guide

## Overview

The **TblAwardsDetailed** table and **sp_CompileAwardsDetailed** stored procedure provide comprehensive award information with all possible combinations from staging tables. This gives System Admins maximum visibility into award data for UI display, decision-making, and tenant assignment.

## Purpose

Unlike `TblAwardsSummary` which provides aggregated statistics, `TblAwardsDetailed` denormalizes all award data into a single table showing:
- Base award information
- All classifications for each award
- All pay rates with their classifications
- All expense allowances
- All wage allowances

This allows System Admins to:
1. **View Complete Award Data** - See all details in one place
2. **Understand Award Structure** - See all combinations of classifications, pay rates, and allowances
3. **Make Informed Decisions** - Have all information needed for tenant assignment
4. **Brief QA/BA Teams** - Provide clear, comprehensive data for testing and analysis

## Database Table: TblAwardsDetailed

### Structure

The table contains 60+ columns organized into categories:

#### Award Basic Info (9 fields)
- `award_code` - Award identifier (e.g., MA000001)
- `award_name` - Full award name
- `award_id`, `award_fixed_id` - FWC identifiers
- `award_operative_from`, `award_operative_to` - Validity dates
- `version_number`, `published_year` - Version tracking

#### Classification Info (6 fields)
- `classification_fixed_id` - Classification identifier
- `classification_name` - Classification title
- `parent_classification_name` - Parent classification
- `classification_level` - Hierarchy level
- `classification_clauses` - Related clauses
- `classification_clause_description` - Clause details

#### Pay Rate Info (7 fields)
- `base_pay_rate_id`, `base_rate_type`, `base_rate` - Base pay information
- `calculated_pay_rate_id`, `calculated_rate_type`, `calculated_rate` - Calculated rates
- `employee_rate_type_code` - Employee type

#### Expense Allowance Info (8 fields)
- `expense_allowance_fixed_id` - Allowance identifier
- `expense_allowance_name` - Allowance description
- `parent_expense_allowance` - Parent allowance
- `expense_allowance_amount` - Amount value
- `expense_payment_frequency` - Payment schedule
- `expense_is_all_purpose` - All-purpose flag
- `expense_last_adjusted_year`, `expense_cpi_quarter` - Adjustment tracking

#### Wage Allowance Info (8 fields)
- `wage_allowance_fixed_id` - Allowance identifier
- `wage_allowance_name` - Allowance description
- `parent_wage_allowance` - Parent allowance
- `wage_allowance_rate`, `wage_allowance_rate_unit` - Rate information
- `wage_allowance_amount` - Amount value
- `wage_payment_frequency` - Payment schedule
- `wage_is_all_purpose` - All-purpose flag

#### Metadata (4 fields)
- `record_type` - Type of record (BASE, WITH_CLASSIFICATION, WITH_PAYRATE, WITH_EXPENSE, WITH_WAGE)
- `is_active` - Active status
- `compiled_at` - Compilation timestamp
- `created_at`, `updated_at` - Audit timestamps

### Record Types

Each award generates multiple records based on available data:

1. **BASE** - One record per award with just basic info
2. **WITH_CLASSIFICATION** - One record per classification within the award
3. **WITH_PAYRATE** - One record per pay rate (includes classification info)
4. **WITH_EXPENSE** - One record per expense allowance
5. **WITH_WAGE** - One record per wage allowance

### Example

For Award MA000001 with:
- 1 base award
- 3 classifications
- 5 pay rates
- 2 expense allowances
- 1 wage allowance

The table will contain: **12 records** (1 base + 3 class + 5 pay + 2 expense + 1 wage)

## Stored Procedure: sp_CompileAwardsDetailed

### Syntax

```sql
EXEC sp_CompileAwardsDetailed [@award_code];
```

### Parameters

- `@award_code` (NVARCHAR(50), optional)
  - Specific award to compile
  - If NULL, compiles ALL awards
  - Example: 'MA000001'

### Returns

Success response with compilation statistics:

| Column | Type | Description |
|--------|------|-------------|
| Status | NVARCHAR | 'Success' or 'Error' |
| TotalRecords | INT | Total records created |
| TotalAwards | INT | Number of unique awards |
| BaseRecords | INT | Count of BASE records |
| ClassificationRecords | INT | Count of WITH_CLASSIFICATION records |
| PayRateRecords | INT | Count of WITH_PAYRATE records |
| ExpenseRecords | INT | Count of WITH_EXPENSE records |
| WageRecords | INT | Count of WITH_WAGE records |
| ErrorMessage | NVARCHAR | Error details if Status = 'Error' |

### Usage Examples

#### Compile All Awards
```sql
EXEC sp_CompileAwardsDetailed;
```

**Example Output:**
```
Status: Success
TotalRecords: 15,234
TotalAwards: 125
BaseRecords: 125
ClassificationRecords: 3,456
PayRateRecords: 8,921
ExpenseRecords: 1,832
WageRecords: 900
```

#### Compile Specific Award
```sql
EXEC sp_CompileAwardsDetailed @award_code = 'MA000001';
```

**Example Output:**
```
Status: Success
TotalRecords: 45
TotalAwards: 1
BaseRecords: 1
ClassificationRecords: 12
PayRateRecords: 24
ExpenseRecords: 5
WageRecords: 3
```

## REST API Endpoints

### POST /api/ruleengine/compile-awards-detailed

Trigger compilation of detailed award data.

**Request:**
```bash
curl -X POST http://localhost:5000/api/ruleengine/compile-awards-detailed \
  -H "Content-Type: application/json" \
  -d '{"awardCode": "MA000001"}'
```

**Response:**
```json
{
  "status": "Success",
  "totalRecords": 45,
  "totalAwards": 1,
  "baseRecords": 1,
  "classificationRecords": 12,
  "payRateRecords": 24,
  "expenseRecords": 5,
  "wageRecords": 3,
  "errorMessage": null
}
```

### GET /api/awardsdetailed

Query detailed award information with filtering.

**Query Parameters:**
- `awardCode` (optional) - Filter by award code
- `recordType` (optional) - Filter by record type (BASE, WITH_CLASSIFICATION, etc.)
- `classificationFixedId` (optional) - Filter by classification

**Examples:**

Get all detailed records for an award:
```bash
curl "http://localhost:5000/api/awardsdetailed?awardCode=MA000001"
```

Get only pay rate records:
```bash
curl "http://localhost:5000/api/awardsdetailed?recordType=WITH_PAYRATE"
```

Get specific classification details:
```bash
curl "http://localhost:5000/api/awardsdetailed?classificationFixedId=12345"
```

**Response:**
```json
[
  {
    "id": 1,
    "awardCode": "MA000001",
    "awardName": "Fast Food Industry Award 2020",
    "awardId": 1234,
    "awardFixedId": 5678,
    "classificationName": "Fast food employee level 1",
    "baseRate": 21.38,
    "recordType": "WITH_PAYRATE",
    ...
  }
]
```

## Use Cases

### 1. System Admin Award Selection UI

Display all awards with complete details:

```sql
-- Get summary of all awards for dropdown
SELECT DISTINCT 
    award_code,
    award_name,
    COUNT(*) as total_configurations
FROM TblAwardsDetailed
GROUP BY award_code, award_name
ORDER BY award_name;
```

### 2. Award Details View

Show all information for selected award:

```sql
-- Get all details for specific award
SELECT * 
FROM TblAwardsDetailed
WHERE award_code = 'MA000001'
ORDER BY record_type, id;
```

### 3. Classification Browser

Browse all classifications across all awards:

```sql
-- Get all unique classifications
SELECT DISTINCT
    award_code,
    award_name,
    classification_name,
    classification_level,
    base_rate
FROM TblAwardsDetailed
WHERE record_type IN ('WITH_CLASSIFICATION', 'WITH_PAYRATE')
  AND classification_name IS NOT NULL
ORDER BY award_name, classification_level;
```

### 4. Pay Rate Comparison

Compare pay rates across awards:

```sql
-- Compare pay rates for similar classifications
SELECT 
    award_code,
    award_name,
    classification_name,
    base_rate,
    calculated_rate,
    employee_rate_type_code
FROM TblAwardsDetailed
WHERE record_type = 'WITH_PAYRATE'
  AND classification_name LIKE '%level 1%'
ORDER BY base_rate DESC;
```

### 5. Allowance Analysis

Analyze allowances across awards:

```sql
-- Get all expense allowances
SELECT 
    award_code,
    award_name,
    expense_allowance_name,
    expense_allowance_amount,
    expense_payment_frequency,
    expense_is_all_purpose
FROM TblAwardsDetailed
WHERE record_type = 'WITH_EXPENSE'
  AND expense_allowance_amount > 0
ORDER BY expense_allowance_amount DESC;
```

### 6. Tenant Assignment Data

Get complete award info for tenant assignment:

```sql
-- Get comprehensive award data for tenant decision
SELECT 
    award_code,
    award_name,
    record_type,
    classification_name,
    base_rate,
    expense_allowance_name,
    wage_allowance_name
FROM TblAwardsDetailed
WHERE award_code = 'MA000001'
ORDER BY record_type, id;
```

## Workflow Integration

### Initial Setup

1. Run ETL pipeline to populate staging tables
2. Execute `sp_CompileAwardsDetailed` to generate detailed data
3. Query `TblAwardsDetailed` for System Admin UI

### Regular Updates

After each ETL pipeline run:

```sql
-- Re-compile all awards with updated data
EXEC sp_CompileAwardsDetailed;

-- Verify compilation
SELECT 
    'TotalRecords' as Metric, COUNT(*) as Value FROM TblAwardsDetailed
UNION ALL
SELECT 'UniqueAwards', COUNT(DISTINCT award_code) FROM TblAwardsDetailed
UNION ALL
SELECT 'LastCompiled', CAST(MAX(compiled_at) AS NVARCHAR) FROM TblAwardsDetailed;
```

### Performance Considerations

- **Indexes**: Pre-created on award_code, record_type, classification_fixed_id
- **Compilation Time**: Approximately 2-5 seconds for 100 awards
- **Storage**: ~2-3 KB per record, expect 50-200 records per award
- **Query Performance**: Filtered queries return in <100ms

## Comparison: Summary vs Detailed

| Feature | TblAwardsSummary | TblAwardsDetailed |
|---------|------------------|-------------------|
| Records per Award | 1 | 50-200+ |
| Data Type | Aggregated | Denormalized |
| Primary Use | Quick statistics | Comprehensive details |
| Best For | Dashboard, charts | Detailed analysis, assignment |
| Refresh Frequency | After each ETL | As needed |
| Query Speed | Very fast | Fast (with filters) |

## Troubleshooting

### Issue: Compilation returns 0 records

**Solution:** Verify staging tables have data
```sql
SELECT 'Awards' as Table, COUNT(*) as Records FROM Stg_TblAwards
UNION ALL
SELECT 'Classifications', COUNT(*) FROM Stg_TblClassifications
UNION ALL
SELECT 'PayRates', COUNT(*) FROM Stg_TblPayRates;
```

### Issue: Missing data for some awards

**Solution:** Check staging table completeness
```sql
-- Check which awards have data in each staging table
SELECT 
    a.code,
    a.name,
    CASE WHEN c.cnt > 0 THEN 'Yes' ELSE 'No' END as Has_Classifications,
    CASE WHEN p.cnt > 0 THEN 'Yes' ELSE 'No' END as Has_PayRates,
    CASE WHEN e.cnt > 0 THEN 'Yes' ELSE 'No' END as Has_Expense,
    CASE WHEN w.cnt > 0 THEN 'Yes' ELSE 'No' END as Has_Wage
FROM Stg_TblAwards a
LEFT JOIN (SELECT award_code, COUNT(*) cnt FROM Stg_TblClassifications GROUP BY award_code) c ON a.code = c.award_code
LEFT JOIN (SELECT award_code, COUNT(*) cnt FROM Stg_TblPayRates GROUP BY award_code) p ON a.code = p.award_code
LEFT JOIN (SELECT award_code, COUNT(*) cnt FROM Stg_TblExpenseAllowances GROUP BY award_code) e ON a.code = e.award_code
LEFT JOIN (SELECT award_code, COUNT(*) cnt FROM Stg_TblWageAllowances GROUP BY award_code) w ON a.code = w.award_code;
```

### Issue: Slow query performance

**Solution:** Use specific filters
```sql
-- Good: Use filters
SELECT * FROM TblAwardsDetailed 
WHERE award_code = 'MA000001' AND record_type = 'WITH_PAYRATE';

-- Avoid: Full table scan
SELECT * FROM TblAwardsDetailed; -- Only for admin reporting
```

## Best Practices

1. **Regular Compilation**: Run after each ETL update
2. **Use Filters**: Always filter by award_code or record_type in queries
3. **Monitor Growth**: Track record counts over time
4. **Archive Old Data**: Consider archiving old versions
5. **UI Pagination**: Implement pagination for large result sets
6. **Cache Results**: Cache frequent queries in application layer

## Reporting Queries

### Award Coverage Report
```sql
SELECT 
    record_type,
    COUNT(DISTINCT award_code) as awards_with_data,
    COUNT(*) as total_records,
    AVG(CAST(COUNT(*) as FLOAT)) as avg_records_per_award
FROM TblAwardsDetailed
GROUP BY record_type
ORDER BY record_type;
```

### Data Completeness Report
```sql
SELECT 
    a.code,
    a.name,
    SUM(CASE WHEN d.record_type = 'BASE' THEN 1 ELSE 0 END) as base,
    SUM(CASE WHEN d.record_type = 'WITH_CLASSIFICATION' THEN 1 ELSE 0 END) as classifications,
    SUM(CASE WHEN d.record_type = 'WITH_PAYRATE' THEN 1 ELSE 0 END) as pay_rates,
    SUM(CASE WHEN d.record_type = 'WITH_EXPENSE' THEN 1 ELSE 0 END) as expenses,
    SUM(CASE WHEN d.record_type = 'WITH_WAGE' THEN 1 ELSE 0 END) as wages
FROM Stg_TblAwards a
LEFT JOIN TblAwardsDetailed d ON a.code = d.award_code
GROUP BY a.code, a.name
ORDER BY a.name;
```
