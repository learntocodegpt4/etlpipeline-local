# Clause Information in Awards Detailed Table

## Overview

The `TblAwardsDetailed` table now captures comprehensive clause information for all award components, enabling the System Admin UI to display which specific clauses from the Fair Work Commission awards apply to each classification, pay rate, and allowance.

## Clause Fields

### Classification Clauses
- **classification_clauses** (NVARCHAR(200)) - Clause numbers (e.g., "13.1", "14.2")
- **classification_clause_description** (NVARCHAR(1000)) - Detailed clause description

### Expense Allowance Clauses
- **expense_clause_fixed_id** (INT) - FWC clause identifier
- **expense_clauses** (NVARCHAR(200)) - Clause numbers

### Wage Allowance Clauses
- **wage_clause_fixed_id** (INT) - FWC clause identifier
- **wage_clauses** (NVARCHAR(200)) - Clause numbers

## Data Flow

```
FWC API Data
    ↓
ETL Pipeline (Python)
    ↓
Staging Tables (with clause info)
    ├── Stg_TblClassifications.clauses
    ├── Stg_TblExpenseAllowances.clause_fixed_id, clauses
    └── Stg_TblWageAllowances.clause_fixed_id, clauses
    ↓
sp_CompileAwardsDetailed (Stored Procedure)
    ↓
TblAwardsDetailed (Comprehensive table with all clauses)
    ↓
REST API Endpoint
    ↓
System Admin UI
```

## Use Cases

### 1. Display Clauses on Award Summary Page

When System Admin views an award, show which clauses define each component:

**SQL Query:**
```sql
SELECT 
    award_code,
    award_name,
    'Classification: ' + classification_name as component,
    classification_clauses as clause_reference,
    classification_clause_description as clause_details
FROM TblAwardsDetailed
WHERE award_code = 'MA000001' 
  AND record_type = 'WITH_CLASSIFICATION'
  AND classification_clauses IS NOT NULL

UNION ALL

SELECT 
    award_code,
    award_name,
    'Expense Allowance: ' + expense_allowance_name,
    expense_clauses,
    'Clause ID: ' + CAST(expense_clause_fixed_id AS NVARCHAR)
FROM TblAwardsDetailed
WHERE award_code = 'MA000001'
  AND record_type = 'WITH_EXPENSE'
  AND expense_clauses IS NOT NULL

UNION ALL

SELECT 
    award_code,
    award_name,
    'Wage Allowance: ' + wage_allowance_name,
    wage_clauses,
    'Clause ID: ' + CAST(wage_clause_fixed_id AS NVARCHAR)
FROM TblAwardsDetailed
WHERE award_code = 'MA000001'
  AND record_type = 'WITH_WAGE'
  AND wage_clauses IS NOT NULL
ORDER BY component;
```

**UI Display Example:**
```
Award: MA000001 - Fast Food Industry Award 2020

Components and Clauses:
┌─────────────────────────────────────────────────────────────────┐
│ Classification: Fast food employee level 1                      │
│ Clause: 13.1                                                    │
│ Description: Entry level position...                            │
├─────────────────────────────────────────────────────────────────┤
│ Expense Allowance: First aid allowance                          │
│ Clause: 18.3                                                    │
│ Clause ID: 45678                                                │
├─────────────────────────────────────────────────────────────────┤
│ Wage Allowance: Leading hand allowance                          │
│ Clause: 19.2                                                    │
│ Clause ID: 45679                                                │
└─────────────────────────────────────────────────────────────────┘
```

### 2. Clause Compliance Verification for QA

QA testers can verify that data is correctly mapped to clauses:

```sql
-- Check if all allowances have clause references
SELECT 
    record_type,
    COUNT(*) as total_records,
    SUM(CASE WHEN expense_clauses IS NOT NULL OR wage_clauses IS NOT NULL THEN 1 ELSE 0 END) as with_clauses,
    SUM(CASE WHEN expense_clauses IS NULL AND wage_clauses IS NULL THEN 1 ELSE 0 END) as without_clauses
FROM TblAwardsDetailed
WHERE record_type IN ('WITH_EXPENSE', 'WITH_WAGE')
GROUP BY record_type;
```

### 3. Business Analyst Award Structure Analysis

BA can analyze which clauses are most commonly used:

```sql
-- Find most frequently used clauses
SELECT 
    clause_reference,
    COUNT(DISTINCT award_code) as awards_using_clause,
    COUNT(*) as total_occurrences,
    STRING_AGG(award_name, ', ') as awards
FROM (
    SELECT award_code, award_name, classification_clauses as clause_reference
    FROM TblAwardsDetailed 
    WHERE classification_clauses IS NOT NULL
    UNION ALL
    SELECT award_code, award_name, expense_clauses
    FROM TblAwardsDetailed 
    WHERE expense_clauses IS NOT NULL
    UNION ALL
    SELECT award_code, award_name, wage_clauses
    FROM TblAwardsDetailed 
    WHERE wage_clauses IS NOT NULL
) clauses
GROUP BY clause_reference
ORDER BY awards_using_clause DESC, total_occurrences DESC;
```

### 4. Tenant Assignment with Clause Information

When assigning award to tenant, show relevant clauses:

```sql
-- Get award details for tenant assignment screen
SELECT 
    award_code,
    award_name,
    record_type,
    CASE record_type
        WHEN 'WITH_CLASSIFICATION' THEN classification_name
        WHEN 'WITH_EXPENSE' THEN expense_allowance_name
        WHEN 'WITH_WAGE' THEN wage_allowance_name
    END as component_name,
    CASE record_type
        WHEN 'WITH_CLASSIFICATION' THEN classification_clauses
        WHEN 'WITH_EXPENSE' THEN expense_clauses
        WHEN 'WITH_WAGE' THEN wage_clauses
    END as applicable_clause,
    CASE record_type
        WHEN 'WITH_PAYRATE' THEN base_rate
        WHEN 'WITH_EXPENSE' THEN expense_allowance_amount
        WHEN 'WITH_WAGE' THEN wage_allowance_amount
    END as rate_or_amount
FROM TblAwardsDetailed
WHERE award_code = @SelectedAwardCode
  AND record_type != 'BASE'
ORDER BY record_type, component_name;
```

## API Integration

### Get Award Details with Clauses

**Request:**
```bash
GET /api/awardsdetailed?awardCode=MA000001
```

**Response (Sample):**
```json
[
  {
    "awardCode": "MA000001",
    "awardName": "Fast Food Industry Award 2020",
    "recordType": "WITH_CLASSIFICATION",
    "classificationName": "Fast food employee level 1",
    "classificationClauses": "13.1",
    "classificationClauseDescription": "Entry level position for fast food employees"
  },
  {
    "awardCode": "MA000001",
    "awardName": "Fast Food Industry Award 2020",
    "recordType": "WITH_EXPENSE",
    "expenseAllowanceName": "First aid allowance",
    "expenseClauseFixedId": 45678,
    "expenseClauses": "18.3",
    "expenseAllowanceAmount": 15.85
  },
  {
    "awardCode": "MA000001",
    "awardName": "Fast Food Industry Award 2020",
    "recordType": "WITH_WAGE",
    "wageAllowanceName": "Leading hand allowance",
    "wageClauseFixedId": 45679,
    "wageClauses": "19.2",
    "wageAllowanceAmount": 3.50
  }
]
```

### Filter by Specific Clause

**Request:**
```bash
# Get all components that reference clause 13.1
GET /api/awardsdetailed?recordType=WITH_CLASSIFICATION
```

Then filter in application code or use custom query.

## React UI Component Example

```javascript
const AwardClauseDisplay = ({ awardCode }) => {
  const [awardDetails, setAwardDetails] = useState([]);

  useEffect(() => {
    fetch(`/api/awardsdetailed?awardCode=${awardCode}`)
      .then(r => r.json())
      .then(data => setAwardDetails(data));
  }, [awardCode]);

  // Group by record type
  const classifications = awardDetails.filter(d => 
    d.recordType === 'WITH_CLASSIFICATION' && d.classificationClauses
  );
  
  const expenseAllowances = awardDetails.filter(d => 
    d.recordType === 'WITH_EXPENSE' && d.expenseClauses
  );
  
  const wageAllowances = awardDetails.filter(d => 
    d.recordType === 'WITH_WAGE' && d.wageClauses
  );

  return (
    <div>
      <h3>Classifications</h3>
      {classifications.map(c => (
        <div key={c.id}>
          <strong>{c.classificationName}</strong>
          <span>Clause: {c.classificationClauses}</span>
          <p>{c.classificationClauseDescription}</p>
        </div>
      ))}

      <h3>Expense Allowances</h3>
      {expenseAllowances.map(e => (
        <div key={e.id}>
          <strong>{e.expenseAllowanceName}</strong>
          <span>Clause: {e.expenseClauses}</span>
          <span>Amount: ${e.expenseAllowanceAmount}</span>
        </div>
      ))}

      <h3>Wage Allowances</h3>
      {wageAllowances.map(w => (
        <div key={w.id}>
          <strong>{w.wageAllowanceName}</strong>
          <span>Clause: {w.wageClauses}</span>
          <span>Amount: ${w.wageAllowanceAmount}</span>
        </div>
      ))}
    </div>
  );
};
```

## Benefits

### For System Admin
- ✅ See which clauses apply to each award component
- ✅ Understand the legal/compliance basis for each rate or allowance
- ✅ Make informed decisions when assigning awards to tenants
- ✅ Quickly reference FWC award documents

### For QA Testers
- ✅ Verify clause assignments are correct
- ✅ Cross-reference with FWC published awards
- ✅ Identify missing or incorrect clause mappings
- ✅ Generate compliance reports

### For Business Analysts
- ✅ Analyze clause usage patterns
- ✅ Understand award structure complexity
- ✅ Document award configurations
- ✅ Create training materials with clause references

### For Compliance
- ✅ Full audit trail from allowance to clause
- ✅ Easy verification against FWC requirements
- ✅ Support for compliance reporting
- ✅ Evidence for workplace inspections

## Validation Queries

### Check Clause Coverage

```sql
-- Verify all classifications have clauses
SELECT 
    COUNT(*) as total_classifications,
    SUM(CASE WHEN classification_clauses IS NOT NULL THEN 1 ELSE 0 END) as with_clauses,
    SUM(CASE WHEN classification_clauses IS NULL THEN 1 ELSE 0 END) as without_clauses
FROM TblAwardsDetailed
WHERE record_type = 'WITH_CLASSIFICATION';

-- Verify expense allowances have clauses
SELECT 
    COUNT(*) as total_expense_allowances,
    SUM(CASE WHEN expense_clauses IS NOT NULL THEN 1 ELSE 0 END) as with_clauses,
    SUM(CASE WHEN expense_clauses IS NULL THEN 1 ELSE 0 END) as without_clauses
FROM TblAwardsDetailed
WHERE record_type = 'WITH_EXPENSE';

-- Verify wage allowances have clauses
SELECT 
    COUNT(*) as total_wage_allowances,
    SUM(CASE WHEN wage_clauses IS NOT NULL THEN 1 ELSE 0 END) as with_clauses,
    SUM(CASE WHEN wage_clauses IS NULL THEN 1 ELSE 0 END) as without_clauses
FROM TblAwardsDetailed
WHERE record_type = 'WITH_WAGE';
```

### Find Components Without Clauses

```sql
-- Find expense allowances without clause references
SELECT 
    award_code,
    award_name,
    expense_allowance_name,
    expense_allowance_amount
FROM TblAwardsDetailed
WHERE record_type = 'WITH_EXPENSE'
  AND expense_clauses IS NULL
ORDER BY award_code, expense_allowance_name;
```

## Summary

The clause information feature provides:
1. **Complete Visibility**: All clauses captured from staging tables
2. **UI Ready**: Data structured for easy display
3. **Compliance Support**: Full traceability to FWC clauses
4. **QA Friendly**: Easy verification and reporting
5. **BA Analysis**: Rich data for understanding award structure

This makes the `TblAwardsDetailed` table a comprehensive source of truth for System Admin award management with full clause transparency.
