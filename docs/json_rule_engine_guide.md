# JSON-Based Rule Engine Guide

## Overview

The JSON-based rule engine provides a flexible, data-driven approach to calculating pay rates based on Fair Work Commission (FWC) awards. Instead of hardcoded logic, penalty and allowance rules are stored as JSON objects in database tables, allowing for easy updates and complex conditional logic.

## Architecture

### Core Components

1. **TblPenaltyRulesJSON** - Stores penalty rules (casual loading, weekend, overtime, shift penalties)
2. **TblAllowanceRulesJSON** - Stores allowance rules (meal, first aid, sleepover, etc.)
3. **TblRuleExecutionHistory** - Audit trail of rule evaluations
4. **sp_EvaluateJSONPenaltyRules** - Evaluates rules for a single scenario
5. **sp_CalculatePayRatesFromJSONRules** - Bulk calculates all combinations

---

## JSON Rule Structure

### Penalty Rule Format

```json
{
  "rule_id": "MA000120_PEN_001",
  "award_code": "MA000120",
  "name": "Casual Loading",
  "priority": 50,
  "status": "Active",
  "if": {
    "employment_type": ["Casual"]
  },
  "then": {
    "apply_multiplier": 1.25,
    "apply_to": ["hourly_rate"],
    "note": "25% casual loading"
  }
}
```

### Allowance Rule Format

```json
{
  "rule_id": "MA000120_ALW_001",
  "award_code": "MA000120",
  "name": "Meal Allowance - Late Finish",
  "priority": 100,
  "status": "Active",
  "if": {
    "shift_duration_hours": {"gte": 5},
    "shift_end_time": {"gte": "19:00"}
  },
  "then": {
    "apply_flat_amount": 17.07,
    "frequency": "per_shift",
    "note": "Meal allowance for shift > 5 hours ending after 7pm"
  }
}
```

---

## Condition Types

### Employment Type Conditions

```json
"if": {
  "employment_type": ["Casual"]
}
```

Matches: `FULL_TIME`, `PART_TIME`, `CASUAL`

### Day/Time Conditions

```json
"when": {
  "day_of_week": ["Saturday"],
  "start_time": "00:00",
  "end_time": "23:59"
}
```

Matches specific days: `Monday`, `Tuesday`, `Wednesday`, `Thursday`, `Friday`, `Saturday`, `Sunday`

```json
"when": {
  "day_type": ["public_holiday"]
}
```

Matches day types: `weekday`, `weekend`, `public_holiday`

### Shift Type Conditions

```json
"when": {
  "shift_type": ["night"],
  "time_range": {"start": "22:00", "end": "07:00"}
}
```

Shift types: `standard`, `night`, `afternoon`, `evening`, `sleepover`

### Comparison Operators

```json
"if": {
  "overtime_hours": {"lte": 2}
}
```

Operators: `gt` (greater than), `gte` (≥), `lt` (less than), `lte` (≤), `eq` (equals)

### Duration Conditions

```json
"if": {
  "shift_duration_hours": {"gte": 5}
}
```

### Employee Attribute Conditions

```json
"if": {
  "has_first_aid_certificate": true,
  "is_first_aid_officer": true
}
```

---

## Action Types

### Multiplier Actions

```json
"then": {
  "apply_multiplier": 1.5,
  "apply_to": ["hourly_rate"],
  "note": "Saturday penalty"
}
```

**Calculation:** `new_rate = base_rate × multiplier`

Example: `$25.00 × 1.5 = $37.50`

### Flat Amount Actions

```json
"then": {
  "apply_flat_amount": 17.07,
  "frequency": "per_shift",
  "note": "Meal allowance"
}
```

**Calculation:** `total_pay = calculated_rate + flat_amount`

Example: `$25.00 + $17.07 = $42.07`

### Combined Actions

For compound scenarios (e.g., Casual + Saturday):

1. Apply casual loading: `$25.00 × 1.25 = $31.25`
2. Apply Saturday penalty: `$31.25 × 1.5 = $46.88`

---

## Sample Rules for MA000120

### Rule 1: Casual Loading
```json
{
  "rule_id": "MA000120_PEN_001",
  "award_code": "MA000120",
  "name": "Casual Loading",
  "priority": 50,
  "status": "Active",
  "if": {
    "employment_type": ["Casual"]
  },
  "then": {
    "apply_multiplier": 1.25,
    "apply_to": ["hourly_rate"],
    "note": "25% casual loading"
  }
}
```

**FWC Reference:** Clause 10.4

**Example Calculation:**
```
Base rate: $25.00/hour
Casual rate: $25.00 × 1.25 = $31.25/hour
```

### Rule 2: Saturday Ordinary Hours
```json
{
  "rule_id": "MA000120_PEN_002",
  "award_code": "MA000120",
  "name": "Saturday Ordinary Hours",
  "priority": 100,
  "status": "Active",
  "when": {
    "day_of_week": ["Saturday"],
    "start_time": "00:00",
    "end_time": "23:59"
  },
  "then": {
    "apply_multiplier": 1.5,
    "apply_to": ["hourly_rate"],
    "note": "Saturday ordinary hours penalty"
  }
}
```

**FWC Reference:** Clause 25.5(a)

**Example Calculation:**
```
Full-time Saturday:
Base rate: $25.00/hour
Saturday rate: $25.00 × 1.5 = $37.50/hour

Casual Saturday:
Base rate: $25.00/hour
Casual rate: $25.00 × 1.25 = $31.25/hour
Saturday rate: $31.25 × 1.5 = $46.88/hour
```

### Rule 3: Saturday Overtime - First 2 Hours
```json
{
  "rule_id": "MA000120_PEN_003",
  "award_code": "MA000120",
  "name": "Saturday Overtime First 2 Hours",
  "priority": 110,
  "status": "Active",
  "when": {
    "day_of_week": ["Saturday"]
  },
  "if": {
    "overtime_hours": {"lte": 2}
  },
  "then": {
    "apply_multiplier": 1.5,
    "apply_to": ["overtime"],
    "note": "First two hours overtime Saturday"
  }
}
```

**FWC Reference:** Clause 28.2(a)

### Rule 4: Sunday All Hours
```json
{
  "rule_id": "MA000120_PEN_005",
  "award_code": "MA000120",
  "name": "Sunday All Hours",
  "priority": 130,
  "status": "Active",
  "when": {
    "day_of_week": ["Sunday"]
  },
  "then": {
    "apply_multiplier": 2.0,
    "apply_to": ["hourly_rate", "overtime"],
    "note": "Sunday penalty"
  }
}
```

**FWC Reference:** Clause 25.5(b)

**Example Calculation:**
```
Full-time Sunday:
Base rate: $25.00/hour
Sunday rate: $25.00 × 2.0 = $50.00/hour

Casual Sunday:
Base rate: $25.00/hour
Casual rate: $25.00 × 1.25 = $31.25/hour
Sunday rate: $31.25 × 2.0 = $62.50/hour
```

### Rule 5: Public Holiday
```json
{
  "rule_id": "MA000120_PEN_006",
  "award_code": "MA000120",
  "name": "Public Holiday",
  "priority": 200,
  "status": "Active",
  "when": {
    "day_type": ["public_holiday"]
  },
  "then": {
    "apply_multiplier": 2.5,
    "apply_to": ["hourly_rate", "overtime"],
    "note": "Public holiday penalty"
  }
}
```

**FWC Reference:** Clause 29.2

**Example Calculation:**
```
Base rate: $25.00/hour
Public holiday rate: $25.00 × 2.5 = $62.50/hour
```

### Rule 6: Night Shift Penalty
```json
{
  "rule_id": "MA000120_PEN_007",
  "award_code": "MA000120",
  "name": "Night Shift Penalty",
  "priority": 90,
  "status": "Active",
  "when": {
    "shift_type": ["night"],
    "time_range": {"start": "22:00", "end": "07:00"}
  },
  "then": {
    "apply_multiplier": 1.15,
    "apply_to": ["hourly_rate"],
    "note": "Night shift 15% penalty (10pm-7am)"
  }
}
```

**FWC Reference:** Clause 25.7

**Example Calculation:**
```
Base rate: $25.00/hour
Night shift rate: $25.00 × 1.15 = $28.75/hour
```

### Rule 7: Evening Shift Penalty
```json
{
  "rule_id": "MA000120_PEN_008",
  "award_code": "MA000120",
  "name": "Evening Shift Penalty",
  "priority": 85,
  "status": "Active",
  "when": {
    "shift_type": ["afternoon", "evening"],
    "time_range": {"start": "18:00", "end": "22:00"}
  },
  "then": {
    "apply_multiplier": 1.125,
    "apply_to": ["hourly_rate"],
    "note": "Evening shift 12.5% penalty (6pm-10pm)"
  }
}
```

**FWC Reference:** Clause 25.6

**Example Calculation:**
```
Base rate: $25.00/hour
Evening shift rate: $25.00 × 1.125 = $28.13/hour
```

### Rule 8: Meal Allowance
```json
{
  "rule_id": "MA000120_ALW_001",
  "award_code": "MA000120",
  "name": "Meal Allowance - Late Finish",
  "priority": 100,
  "status": "Active",
  "if": {
    "shift_duration_hours": {"gte": 5},
    "shift_end_time": {"gte": "19:00"}
  },
  "then": {
    "apply_flat_amount": 17.07,
    "frequency": "per_shift",
    "note": "Meal allowance for shift > 5 hours ending after 7pm"
  }
}
```

**FWC Reference:** Clause 20.2(a)

**Example Calculation:**
```
Shift: 09:00 - 20:00 (11 hours, ends after 7pm)
Hourly rate: $25.00
Total hours pay: $25.00 × 11 = $275.00
Meal allowance: $17.07
Total compensation: $275.00 + $17.07 = $292.07
```

---

## Rule Priority

Rules are applied in **ascending priority order** (lower number = higher priority):

| Priority Range | Rule Type | Example |
|---------------|-----------|---------|
| 1-49 | Critical/Override rules | System-wide adjustments |
| 50-79 | Employment type | Casual loading |
| 80-99 | Shift penalties | Night, Evening shifts |
| 100-149 | Day penalties | Saturday, Sunday |
| 150-199 | Overtime | First 2hrs, After 2hrs |
| 200+ | Special days | Public holidays |

### Priority Example

**Scenario:** Casual employee working Saturday night shift

**Rules Applied (in order):**
1. Priority 50: Casual Loading (1.25×)
2. Priority 90: Night Shift (1.15×)
3. Priority 100: Saturday (1.5×)

**Calculation:**
```
Base: $25.00
× Casual 1.25 = $31.25
× Night 1.15 = $35.94
× Saturday 1.5 = $53.91/hour
```

---

## Using the Stored Procedures

### 1. Evaluate Single Scenario

```sql
DECLARE @result TABLE (
    award_code NVARCHAR(50),
    base_rate DECIMAL(18,4),
    employment_type NVARCHAR(50),
    calculated_hourly_rate DECIMAL(18,4),
    total_multiplier_applied DECIMAL(5,4),
    total_allowances DECIMAL(10,2),
    total_compensation DECIMAL(18,4),
    calculation_steps NVARCHAR(MAX),
    rules_applied INT
);

INSERT INTO @result
EXEC sp_EvaluateJSONPenaltyRules
    @award_code = 'MA000120',
    @classification_fixed_id = NULL,
    @base_rate = 25.00,
    @employment_type = 'CASUAL',
    @day_of_week = 'Sunday',
    @day_type = 'weekend',
    @shift_type = 'standard',
    @shift_start_time = '09:00',
    @shift_end_time = '17:00',
    @shift_duration_hours = 8.0,
    @overtime_hours = 0,
    @employee_age = 25,
    @is_first_aid_officer = 0,
    @return_details = 1;

SELECT * FROM @result;
```

**Expected Output:**
```
award_code: MA000120
base_rate: 25.00
employment_type: CASUAL
calculated_hourly_rate: 62.50
total_multiplier_applied: 2.50
total_allowances: 0.00
total_compensation: 62.50
calculation_steps: Base: $25.00 × Casual Loading 1.25 = $31.25 × Sunday All Hours 2.0 = $62.50
rules_applied: 2
```

### 2. Bulk Calculate All Combinations

```sql
EXEC sp_CalculatePayRatesFromJSONRules
    @award_code = 'MA000120',
    @classification_fixed_id = NULL;
```

**This generates:**
- All employment type combinations (Full-time, Part-time, Casual)
- All day type combinations (Weekday, Saturday, Sunday, Public Holiday)
- All shift type combinations (Standard, Night, Evening)
- Stores results in `TblCalculatedPayRates`

**Expected Records per Classification:**
- 10 base scenarios (full-time weekday, casual Saturday, etc.)
- Additional overtime scenarios
- Additional junior rate scenarios
- **Total: ~50-100 records per classification**

### 3. Query Calculated Rates

```sql
-- Get all casual Sunday rates
SELECT 
    award_code,
    classification_name,
    base_rate,
    calculated_hourly_rate,
    calculation_steps
FROM TblCalculatedPayRates
WHERE award_code = 'MA000120'
    AND employment_type = 'CASUAL'
    AND day_type = 'weekend'
    AND shift_type = 'standard'
    AND CHARINDEX('Sunday', calculation_steps) > 0
ORDER BY classification_name;
```

### 4. View Rule Execution History

```sql
-- See which rules were applied in recent calculations
SELECT 
    rule_id,
    award_code,
    employment_type,
    day_of_week,
    shift_start_time,
    condition_met,
    rule_applied,
    multiplier_applied,
    calculated_rate,
    calculation_note,
    executed_at
FROM TblRuleExecutionHistory
WHERE award_code = 'MA000120'
    AND executed_at >= DATEADD(HOUR, -1, GETUTCDATE())
ORDER BY executed_at DESC;
```

---

## Adding New Rules

### Step 1: Insert Rule into Database

```sql
INSERT INTO TblPenaltyRulesJSON (
    rule_id, award_code, rule_name, priority, status,
    condition_json, action_json, full_rule_json,
    effective_from, clause_reference
)
VALUES (
    'MA000120_PEN_011',
    'MA000120',
    'My Custom Rule',
    95,
    'Active',
    '{"day_of_week": ["Friday"], "time_range": {"start": "20:00", "end": "23:59"}}',
    '{"apply_multiplier": 1.3, "apply_to": ["hourly_rate"], "note": "Friday night penalty"}',
    '{"rule_id": "MA000120_PEN_011", "award_code": "MA000120", "name": "My Custom Rule", "priority": 95, "status": "Active", "when": {"day_of_week": ["Friday"], "time_range": {"start": "20:00", "end": "23:59"}}, "then": {"apply_multiplier": 1.3, "apply_to": ["hourly_rate"], "note": "Friday night penalty"}}',
    '2024-01-01',
    'Clause XX.X'
);
```

### Step 2: Recalculate Rates

```sql
EXEC sp_CalculatePayRatesFromJSONRules
    @award_code = 'MA000120';
```

### Step 3: Verify Results

```sql
SELECT * FROM TblRuleExecutionHistory
WHERE rule_id = 'MA000120_PEN_011'
ORDER BY executed_at DESC;
```

---

## Rule Management Best Practices

### 1. Use Meaningful Rule IDs
- Format: `{AWARD_CODE}_{TYPE}_{NUMBER}`
- Example: `MA000120_PEN_001`, `MA000120_ALW_001`

### 2. Set Appropriate Priorities
- Leave gaps between priorities for future rules
- Group related rules in same priority range

### 3. Include FWC Clause References
- Always reference the specific FWC clause
- Include full clause description for audit

### 4. Test Rules Before Activation
- Set status to 'Draft' initially
- Test with sp_EvaluateJSONPenaltyRules
- Change to 'Active' after verification

### 5. Version Control
- Keep `full_rule_json` populated
- Track changes in `updated_at` and `updated_by`
- Export rules regularly for backup

### 6. Deactivation vs Deletion
- Set `status = 'Inactive'` instead of deleting
- Set `is_active = 0` to exclude from calculations
- Keep historical records for audit

---

## API Integration

### .NET API Endpoints

The JSON rule engine integrates with the existing .NET API:

```csharp
// Calculate pay rate for specific scenario
POST /api/calculatedpayrates/calculate-json
{
  "awardCode": "MA000120",
  "classificationFixedId": 123,
  "baseRate": 25.00,
  "employmentType": "CASUAL",
  "dayOfWeek": "Sunday",
  "shiftType": "standard"
}

// Response
{
  "calculatedRate": 62.50,
  "calculationSteps": "Base: $25.00 × Casual Loading 1.25 = $31.25 × Sunday All Hours 2.0 = $62.50",
  "rulesApplied": 2,
  "allowances": 0.00
}
```

### Query Calculated Rates

```csharp
GET /api/calculatedpayrates?awardCode=MA000120&employmentType=CASUAL&dayType=weekend
```

---

## Troubleshooting

### Rule Not Applied

**Problem:** Rule exists but doesn't affect calculations

**Checks:**
1. Is `status = 'Active'`?
2. Is `is_active = 1`?
3. Is current date within `effective_from` and `effective_to`?
4. Does the condition match the scenario exactly?
5. Check priority - is a higher priority rule overriding?

**Debug Query:**
```sql
SELECT * FROM TblPenaltyRulesJSON
WHERE rule_id = 'MA000120_PEN_XXX';

SELECT * FROM TblRuleExecutionHistory
WHERE rule_id = 'MA000120_PEN_XXX'
ORDER BY executed_at DESC;
```

### Incorrect Calculation

**Problem:** Calculated rate doesn't match expected value

**Checks:**
1. Review `TblRuleExecutionHistory` to see which rules were applied
2. Check rule priority order
3. Verify multipliers are correct (1.5 for 150%, not 0.5)
4. Check if multiple rules are compounding unexpectedly

**Debug:**
```sql
EXEC sp_EvaluateJSONPenaltyRules
    @award_code = 'MA000120',
    @base_rate = 25.00,
    @employment_type = 'CASUAL',
    @day_of_week = 'Sunday',
    @return_details = 1;

-- This returns all applied rules and calculation steps
```

### Performance Issues

**Problem:** Bulk calculation taking too long

**Solutions:**
1. Index optimization already in place
2. Calculate specific award instead of all awards
3. Calculate specific classification instead of all
4. Run during off-peak hours
5. Consider batch processing

---

## Summary

### Benefits of JSON Rule Engine

✅ **Flexible** - Easy to add/modify rules without code changes  
✅ **Auditable** - Complete execution history  
✅ **Scalable** - Handles 1000s of rules efficiently  
✅ **Testable** - Test rules before activation  
✅ **Maintainable** - Rules stored as data, not code  
✅ **FWC Compliant** - Direct mapping to FWC clauses  
✅ **Transparent** - Human-readable calculation steps  

### Key Features

- **10 Penalty Rules** for MA000120 (casual, weekend, overtime, shift)
- **3 Allowance Rules** for MA000120 (meal, sleepover, first aid)
- **Priority-based Execution** - Correct order of operations
- **Compound Calculations** - Supports complex scenarios
- **Audit Trail** - Every rule evaluation logged
- **API Integration** - REST endpoints for UI

### Next Steps

1. Review and test existing MA000120 rules
2. Add rules for additional awards
3. Integrate with front-end UI for System Admin
4. Set up automated rule testing
5. Configure alerts for rule failures

---

**Documentation Version:** 1.0  
**Last Updated:** 2024-12-16  
**Award Coverage:** MA000120 (SCHADS Award)  
**Total Rules:** 13 (10 penalty + 3 allowance)
