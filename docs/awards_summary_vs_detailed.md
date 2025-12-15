# Awards Data Structures Comparison

## Overview

The Rule Engine provides two complementary tables for different use cases:

1. **TblAwardsSummary** - Aggregated statistics (fast overview)
2. **TblAwardsDetailed** - Comprehensive details (complete information)

## Data Structure Comparison

### TblAwardsSummary (Aggregated)

```
Award: MA000001 "Fast Food Industry Award 2020"
┌────────────────────────────────────────────────────────┐
│ TblAwardsSummary - ONE RECORD PER AWARD                │
├────────────────────────────────────────────────────────┤
│ award_code: MA000001                                   │
│ award_name: Fast Food Industry Award 2020             │
│ total_classifications: 12                              │
│ total_pay_rates: 45                                    │
│ total_expense_allowances: 8                            │
│ total_wage_allowances: 5                               │
│ min_base_rate: 21.38                                   │
│ max_base_rate: 38.56                                   │
│ avg_base_rate: 28.45                                   │
└────────────────────────────────────────────────────────┘

Purpose: Quick overview, dashboard statistics
Best for: Charts, summaries, filtering awards
Query speed: Very fast (1 record per award)
```

### TblAwardsDetailed (Denormalized)

```
Award: MA000001 "Fast Food Industry Award 2020"
┌────────────────────────────────────────────────────────┐
│ TblAwardsDetailed - MULTIPLE RECORDS PER AWARD         │
├────────────────────────────────────────────────────────┤
│ Record 1: BASE                                         │
│   award_code: MA000001                                 │
│   award_name: Fast Food Industry Award 2020           │
│   award_id: 1234                                       │
│   operative_from: 2020-02-01                           │
│   [No classification, pay rate, or allowance data]     │
├────────────────────────────────────────────────────────┤
│ Record 2-13: WITH_CLASSIFICATION (12 records)         │
│   award_code: MA000001                                 │
│   classification_name: "Fast food employee level 1"   │
│   classification_level: 1                              │
│   parent_classification_name: NULL                     │
│   clauses: "13.1"                                      │
├────────────────────────────────────────────────────────┤
│ Record 14-58: WITH_PAYRATE (45 records)               │
│   award_code: MA000001                                 │
│   classification_name: "Fast food employee level 1"   │
│   base_rate: 21.38                                     │
│   base_rate_type: "Hourly"                             │
│   employee_rate_type_code: "Adult"                     │
├────────────────────────────────────────────────────────┤
│ Record 59-66: WITH_EXPENSE (8 records)                │
│   award_code: MA000001                                 │
│   expense_allowance_name: "First aid allowance"       │
│   expense_allowance_amount: 15.85                      │
│   expense_payment_frequency: "Weekly"                  │
├────────────────────────────────────────────────────────┤
│ Record 67-71: WITH_WAGE (5 records)                   │
│   award_code: MA000001                                 │
│   wage_allowance_name: "Leading hand allowance"       │
│   wage_allowance_rate: 1.15                            │
│   wage_allowance_amount: 3.50                          │
└────────────────────────────────────────────────────────┘

Purpose: Complete details, tenant assignment, QA/BA analysis
Best for: Detailed views, decision-making, data verification
Query speed: Fast (with filters on award_code or record_type)
Total Records: 71 (1 base + 12 class + 45 pay + 8 expense + 5 wage)
```

## Use Case Matrix

| Scenario | Use TblAwardsSummary | Use TblAwardsDetailed |
|----------|----------------------|------------------------|
| Dashboard showing award counts | ✅ | ❌ |
| Chart of average pay rates | ✅ | ❌ |
| Quick award filtering | ✅ | ❌ |
| Select award for tenant | ✅ | ✅ |
| View all classifications for award | ❌ | ✅ |
| See all pay rates with details | ❌ | ✅ |
| Analyze allowances | ❌ | ✅ |
| QA data verification | ❌ | ✅ |
| BA understanding award structure | ❌ | ✅ |
| Export complete award data | ❌ | ✅ |

## API Endpoints Comparison

### Summary Endpoints

```bash
# Compile summary (aggregated statistics)
POST /api/ruleengine/compile-awards
{
  "awardCode": "MA000001"  # optional
}

Response:
{
  "status": "Success",
  "recordsCompiled": 1      # One record per award
}

# Get awards summary
GET /api/awards?awardCode=MA000001

Response:
[
  {
    "awardCode": "MA000001",
    "awardName": "Fast Food Industry Award 2020",
    "totalClassifications": 12,
    "totalPayRates": 45,
    "minBaseRate": 21.38,
    "maxBaseRate": 38.56
  }
]
```

### Detailed Endpoints

```bash
# Compile detailed (all combinations)
POST /api/ruleengine/compile-awards-detailed
{
  "awardCode": "MA000001"  # optional
}

Response:
{
  "status": "Success",
  "totalRecords": 71,       # All combination records
  "totalAwards": 1,
  "baseRecords": 1,
  "classificationRecords": 12,
  "payRateRecords": 45,
  "expenseRecords": 8,
  "wageRecords": 5
}

# Get detailed awards
GET /api/awardsdetailed?awardCode=MA000001&recordType=WITH_PAYRATE

Response:
[
  {
    "awardCode": "MA000001",
    "awardName": "Fast Food Industry Award 2020",
    "classificationName": "Fast food employee level 1",
    "baseRate": 21.38,
    "baseRateType": "Hourly",
    "employeeRateTypeCode": "Adult",
    "recordType": "WITH_PAYRATE"
  },
  // ... 44 more pay rate records
]
```

## System Admin UI Workflow

### Initial Load
```
1. User opens System Admin Award Management UI
2. Call GET /api/awards to get award list with statistics
3. Display awards in dropdown/table with counts
```

### Award Selection
```
4. User selects award "MA000001" from list
5. Call GET /api/awardsdetailed?awardCode=MA000001
6. Display comprehensive award details organized by record_type:
   - Base info section
   - Classifications table (12 rows)
   - Pay rates table (45 rows)
   - Expense allowances table (8 rows)
   - Wage allowances table (5 rows)
```

### Tenant Assignment
```
7. User reviews all details
8. User clicks "Assign to Tenant XYZ"
9. System has complete award data for assignment
```

## Database Storage Comparison

```
Award: MA000001 with typical data

TblAwardsSummary:
- Records: 1
- Storage: ~500 bytes
- Query time: <1ms

TblAwardsDetailed:
- Records: 50-200 (varies by award)
- Storage: ~2-3 KB per record = 100-600 KB
- Query time (filtered): <50ms
- Query time (unfiltered): <200ms

Recommendation: Use both tables
- Summary for lists and statistics
- Detailed for viewing and decision-making
```

## Record Type Breakdown

### BASE Record
```sql
SELECT * FROM TblAwardsDetailed 
WHERE award_code = 'MA000001' AND record_type = 'BASE';

Purpose: Award metadata only
Contains: Award name, ID, operative dates, version
Missing: All classification, pay, allowance data
Count: Always 1 per award
```

### WITH_CLASSIFICATION Records
```sql
SELECT * FROM TblAwardsDetailed 
WHERE award_code = 'MA000001' AND record_type = 'WITH_CLASSIFICATION';

Purpose: Show all classifications
Contains: Award + Classification details
Missing: Pay rates, allowances
Count: Number of classifications in award
```

### WITH_PAYRATE Records
```sql
SELECT * FROM TblAwardsDetailed 
WHERE award_code = 'MA000001' AND record_type = 'WITH_PAYRATE';

Purpose: Show all pay rates with classifications
Contains: Award + Classification + Pay rate details
Missing: Allowances
Count: Number of pay rates in award
Use: Most important for tenant decisions
```

### WITH_EXPENSE Records
```sql
SELECT * FROM TblAwardsDetailed 
WHERE award_code = 'MA000001' AND record_type = 'WITH_EXPENSE';

Purpose: Show all expense allowances
Contains: Award + Expense allowance details
Missing: Classifications, pay rates, wage allowances
Count: Number of expense allowances in award
```

### WITH_WAGE Records
```sql
SELECT * FROM TblAwardsDetailed 
WHERE award_code = 'MA000001' AND record_type = 'WITH_WAGE';

Purpose: Show all wage allowances
Contains: Award + Wage allowance details
Missing: Classifications, pay rates, expense allowances
Count: Number of wage allowances in award
```

## Performance Characteristics

### TblAwardsSummary
```
Compilation time: 2-3 seconds for 100 awards
Record count: 100 records (1 per award)
Index scans: Very fast (single award lookup)
Best for: Real-time filtering, dashboard updates
```

### TblAwardsDetailed
```
Compilation time: 5-10 seconds for 100 awards
Record count: 5,000-15,000 records (50-150 per award)
Index scans: Fast with filters, moderate without
Best for: Detailed analysis, batch processing
Recommendation: Always use WHERE clause with award_code or record_type
```

## Integration Example

### React UI Component
```javascript
// Step 1: Load award list
const awards = await fetch('/api/awards').then(r => r.json());

// Display summary in dropdown
<select onChange={handleAwardSelect}>
  {awards.map(a => (
    <option value={a.awardCode}>
      {a.awardName} ({a.totalPayRates} pay rates)
    </option>
  ))}
</select>

// Step 2: Load detailed data when selected
const loadAwardDetails = async (awardCode) => {
  const details = await fetch(
    `/api/awardsdetailed?awardCode=${awardCode}`
  ).then(r => r.json());
  
  // Group by record type
  const grouped = {
    base: details.filter(d => d.recordType === 'BASE'),
    classifications: details.filter(d => d.recordType === 'WITH_CLASSIFICATION'),
    payRates: details.filter(d => d.recordType === 'WITH_PAYRATE'),
    expenses: details.filter(d => d.recordType === 'WITH_EXPENSE'),
    wages: details.filter(d => d.recordType === 'WITH_WAGE')
  };
  
  return grouped;
};

// Display in sections
<AwardDetailView>
  <Section title="Pay Rates" data={grouped.payRates} />
  <Section title="Classifications" data={grouped.classifications} />
  <Section title="Allowances" data={[...grouped.expenses, ...grouped.wages]} />
</AwardDetailView>
```

## Conclusion

Both tables serve specific purposes:

✅ **Use TblAwardsSummary for:**
- Award lists and dropdowns
- Dashboard statistics
- Quick filtering
- Performance-critical operations

✅ **Use TblAwardsDetailed for:**
- Complete award information display
- Tenant assignment decisions
- QA data verification
- BA structural analysis
- Detailed reporting

Together, they provide a complete solution for System Admin award management.
