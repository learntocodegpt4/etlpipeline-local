# TblAwardsDetailed Data Structure Explanation

## Overview

The `TblAwardsDetailed` table uses a **denormalized, multi-record approach** where each award generates multiple records based on different data types. This is by design to support flexible querying and UI display.

## Why Many Columns Are NULL

Each record type populates different columns. This is **intentional** and **correct**:

| Record Type | Populated Columns | NULL Columns |
|-------------|-------------------|--------------|
| BASE | Award basic info only | All classification, pay rate, allowance columns |
| WITH_CLASSIFICATION | Award + Classification info | Pay rate and allowance columns |
| WITH_PAYRATE | Award + Classification + Pay rate info | Allowance columns |
| WITH_EXPENSE | Award + Expense allowance info | Classification, pay rate, wage columns |
| WITH_WAGE | Award + Wage allowance info | Classification, pay rate, expense columns |

## Example: Award MA000120 (Children's Services Award 2010)

### Record Breakdown
```
Total Records: 1,111
├── BASE: 1 record
├── WITH_CLASSIFICATION: 479 records
├── WITH_PAYRATE: 479 records
├── WITH_EXPENSE: 104 records
└── WITH_WAGE: 48 records
```

### Sample Records

#### BASE Record (ID: 120)
```
award_code: MA000120
award_name: Children's Services Award 2010
award_id: 1870
award_operative_from: 2010-01-01
record_type: BASE

NULL fields: All classification, pay rate, and allowance columns
```

#### WITH_CLASSIFICATION Record (ID: 32904)
```
award_code: MA000120
award_name: Children's Services Award 2010
classification_fixed_id: 4623
classification_name: Children's Services Employee—Director
classification_clauses: 14.1
classification_clause_description: Children's services employees
record_type: WITH_CLASSIFICATION

NULL fields: Pay rate and allowance columns
```

#### WITH_PAYRATE Record (ID: 117138)
```
award_code: MA000120
award_name: Children's Services Award 2010
classification_fixed_id: 4591
classification_name: Level 1.1
parent_classification_name: Support Worker - On commencement
classification_level: 1
base_pay_rate_id: BR93443
base_rate_type: Weekly
base_rate: 948.0000
calculated_pay_rate_id: CR27706
calculated_rate_type: Hourly
calculated_rate: 24.9500
employee_rate_type_code: AD (Adult)
record_type: WITH_PAYRATE

NULL fields: Allowance columns
```

#### WITH_EXPENSE Record (ID: 165741)
```
award_code: MA000120
award_name: Children's Services Award 2010
expense_allowance_fixed_id: 748
expense_clause_fixed_id: 2372
expense_clauses: 15.3
expense_allowance_name: Excess fares allowance
expense_allowance_amount: 16.8600
expense_payment_frequency: per day
expense_is_all_purpose: 0
expense_last_adjusted_year: 2024
expense_cpi_quarter: March Quarter
record_type: WITH_EXPENSE

NULL fields: Classification and pay rate columns
```

#### WITH_WAGE Record
```
award_code: MA000120
award_name: Children's Services Award 2010
wage_allowance_fixed_id: [value]
wage_clause_fixed_id: [value]
wage_clauses: [value]
wage_allowance_name: [value]
wage_allowance_rate: [value]
wage_allowance_amount: [value]
record_type: WITH_WAGE

NULL fields: Classification and pay rate columns
```

## How to Query the Data

### Get Complete Award Overview
```sql
SELECT * FROM TblAwardsDetailed 
WHERE award_code = 'MA000120'
ORDER BY record_type, id;
```
Returns: All 1,111 records showing complete award picture

### Get Only Pay Rates
```sql
SELECT 
    award_code,
    classification_name,
    base_rate,
    base_rate_type,
    calculated_rate,
    calculated_rate_type,
    employee_rate_type_code
FROM TblAwardsDetailed
WHERE award_code = 'MA000120' 
  AND record_type = 'WITH_PAYRATE'
ORDER BY classification_level;
```
Returns: 479 records with actual pay rate values

### Get Only Allowances
```sql
-- Expense allowances
SELECT 
    award_code,
    expense_allowance_name,
    expense_allowance_amount,
    expense_payment_frequency,
    expense_clauses
FROM TblAwardsDetailed
WHERE award_code = 'MA000120' 
  AND record_type = 'WITH_EXPENSE';

-- Wage allowances
SELECT 
    award_code,
    wage_allowance_name,
    wage_allowance_amount,
    wage_payment_frequency,
    wage_clauses
FROM TblAwardsDetailed
WHERE award_code = 'MA000120' 
  AND record_type = 'WITH_WAGE';
```

## What Data Is Being Extracted

### Current Implementation
The stored procedure extracts **ALL available data** from staging tables:

1. **Stg_TblAwards** → Award metadata (name, operative dates, version)
2. **Stg_TblClassifications** → All classifications with clause references
3. **Stg_TblPayRates** → All pay rates (base rates, calculated rates, employee types)
4. **Stg_TblExpenseAllowances** → All expense allowances with clauses
5. **Stg_TblWageAllowances** → All wage allowances with clauses

### What's In The Staging Tables

The staging tables contain data extracted from FWC API. For MA000120:
- **479 pay rate variations** covering:
  - Different classification levels (1.1, 1.2, 2.1, etc.)
  - Different experience levels (On commencement, After 1 year, etc.)
  - Different rate types (Weekly, Hourly, Annual)
  - Different employee types (Adult, Junior, Apprentice)
  
- **104 expense allowances** covering various scenarios
- **48 wage allowances** covering various scenarios

### Current Joins

```sql
-- Step 1: Base award
SELECT * FROM Stg_TblAwards

-- Step 2: Award + Classifications
SELECT * FROM Stg_TblAwards a
INNER JOIN Stg_TblClassifications c ON a.code = c.award_code

-- Step 3: Award + Pay Rates
SELECT * FROM Stg_TblAwards a
INNER JOIN Stg_TblPayRates p ON a.code = p.award_code

-- Step 4: Award + Expense Allowances
SELECT * FROM Stg_TblAwards a
INNER JOIN Stg_TblExpenseAllowances e ON a.code = e.award_code

-- Step 5: Award + Wage Allowances
SELECT * FROM Stg_TblAwards a
INNER JOIN Stg_TblWageAllowances w ON a.code = w.award_code
```

## What About Shift Premiums, Holiday Rates, Age-Based Rates?

If you need **calculated rates** for specific scenarios (e.g., night shift, weekend, public holiday), these would need to be:

### Option 1: Already in Staging Tables
If FWC API provides these as separate pay rates, they should already be in `Stg_TblPayRates` with different `base_rate_type` or `employee_rate_type_code` values.

### Option 2: Calculated Rates
If these need to be **calculated** (e.g., night shift = base_rate * 1.5), then we need:
1. A reference table with multiplier rules
2. Additional SP logic to calculate and insert these variations
3. Specification of which scenarios to calculate

### Option 3: Additional Staging Tables
If there are other staging tables with shift/holiday/age data not currently joined, specify:
1. Table names
2. Join keys
3. Which columns to extract

## Conclusion

The current implementation is **working correctly**. It extracts **all available data** from staging tables and creates a denormalized view with:
- ✅ All classifications
- ✅ All pay rates (479 variations for MA000120)
- ✅ All allowances (152 total)
- ✅ All clause references
- ✅ Proper joins between awards and related data

**NULL values are expected and correct** - each record type focuses on specific data and leaves other columns NULL.

For additional contextual rates (age, shift, holiday), please specify:
1. Are they in existing staging tables?
2. Should they be calculated?
3. What are the calculation rules?
