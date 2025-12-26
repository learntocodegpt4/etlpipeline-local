# Pay Calculation System - Implementation Guide

## Overview

This guide explains the complete pay calculation system for FWC awards, covering database structure, calculation logic, API usage, and UI integration.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Python ETL Pipeline                       │
│  Extracts FWC data → Staging Tables (Stg_Tbl*)             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│               SQL Pay Calculation Engine                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Reference Tables                                    │   │
│  │  • TblPenaltyRates (penalties: weekend, night, etc.)│   │
│  │  • TblJuniorRates (age-based percentages)          │   │
│  │  • TblCasualLoadings (casual loading %)            │   │
│  │  • TblAllowanceConditions (conditional allowances)  │   │
│  │  • TblApprenticeRates (apprentice/trainee %)       │   │
│  └─────────────────────────────────────────────────────┘   │
│                       │                                      │
│                       ▼                                      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  sp_CalculateAllPayRates                            │   │
│  │  Reads: Stg_TblPayRates + Reference Tables         │   │
│  │  Generates: ALL possible pay rate combinations      │   │
│  │  Output: TblCalculatedPayRates (500-2000 per award)│   │
│  └─────────────────────────────────────────────────────┘   │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│            .NET Rule Engine Microservice                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  API Endpoints                                       │   │
│  │  • POST /api/calculatedpayrates/calculate           │   │
│  │  • GET /api/calculatedpayrates (with filters)       │   │
│  │  • GET /api/calculatedpayrates/statistics           │   │
│  └─────────────────────────────────────────────────────┘   │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                System Admin UI (React)                       │
│  Displays all pay scenarios with filtering                  │
└─────────────────────────────────────────────────────────────┘
```

## Database Schema

### Reference Tables

#### TblPenaltyRates
Stores FWC-defined penalty multipliers for different scenarios.

**Key Columns:**
- `penalty_type` - SATURDAY, SUNDAY, PUBLIC_HOLIDAY, NIGHT_SHIFT, etc.
- `penalty_multiplier` - e.g., 1.5000 for 150%, 2.0000 for 200%
- `applies_from_time` / `applies_to_time` - Time conditions (e.g., 19:00-23:00)
- `applies_to_employment_type` - FULL_TIME, PART_TIME, CASUAL, ALL

**Example Data:**
```sql
INSERT INTO TblPenaltyRates 
  (award_code, penalty_type, penalty_multiplier, effective_from, clause_reference)
VALUES 
  ('MA000120', 'SATURDAY', 1.5000, '2024-01-01', 'Clause 15.3'),
  ('MA000120', 'SUNDAY', 2.0000, '2024-01-01', 'Clause 15.4'),
  ('MA000120', 'PUBLIC_HOLIDAY', 2.5000, '2024-01-01', 'Clause 15.5'),
  ('MA000120', 'NIGHT_SHIFT', 1.1500, '2024-01-01', 'Clause 16.2');
```

#### TblJuniorRates
Age-based pay percentages for employees under 21.

**Example Data:**
```sql
INSERT INTO TblJuniorRates (award_code, age_from, age_to, junior_percentage, effective_from)
VALUES 
  ('MA000120', 16, 16, 0.5000, '2024-01-01'), -- 50% of adult rate
  ('MA000120', 17, 17, 0.6000, '2024-01-01'), -- 60%
  ('MA000120', 18, 18, 0.7000, '2024-01-01'), -- 70%
  ('MA000120', 19, 19, 0.8500, '2024-01-01'), -- 85%
  ('MA000120', 20, 20, 0.9500, '2024-01-01'); -- 95%
```

#### TblCasualLoadings
Casual employment loading percentages (typically 25%).

**Example Data:**
```sql
INSERT INTO TblCasualLoadings (award_code, casual_loading_percentage, effective_from)
VALUES ('MA000120', 0.2500, '2024-01-01'); -- 25% casual loading
```

### Output Table

#### TblCalculatedPayRates
Master table containing ALL calculated pay rate combinations.

**Key Columns:**
- `award_code`, `classification_name` - Identification
- `base_rate` - Starting rate from Stg_TblPayRates
- `employment_type` - FULL_TIME, PART_TIME, CASUAL
- `employee_age_category` - ADULT, AGE_20, AGE_19, etc.
- `day_type` - WEEKDAY, SATURDAY, SUNDAY, PUBLIC_HOLIDAY
- `shift_type` - STANDARD, NIGHT, AFTERNOON, OVERTIME_FIRST2HR, etc.
- `casual_loading_applied` - e.g., 0.2500 for 25%
- `penalty_multiplier_applied` - e.g., 1.5000 for 150%
- `calculated_hourly_rate` - **Final rate**
- `calculation_steps` - Human-readable formula

**Example Record:**
```
award_code: MA000120
classification_name: Support Worker - Level 1.1
base_rate: 25.00
employment_type: CASUAL
employee_age_category: AGE_18
day_type: SUNDAY
shift_type: STANDARD
casual_loading_applied: 0.2500
casual_loaded_rate: 31.25
penalty_multiplier_applied: 2.0000
calculated_hourly_rate: 62.50
calculation_steps: "Base: $25.00 × Casual 1.25 = $31.25 × Sunday 2.0 = $62.50"
```

## Calculation Logic

### Step-by-Step Process

The `sp_CalculateAllPayRates` stored procedure follows this sequence:

#### 1. Base Rates (Adult, Full-time/Part-time, Weekday, Standard)
```sql
SELECT 
    base_rate = CASE 
        WHEN base_rate_type = 'Hourly' THEN base_rate
        WHEN base_rate_type = 'Weekly' THEN base_rate / 38.0
        WHEN base_rate_type = 'Annual' THEN base_rate / 1976.0
    END
FROM Stg_TblPayRates
```

**Example:**
```
Input: Base rate $948.00 (Weekly)
Output: $948.00 / 38 = $24.95/hour
```

#### 2. Casual Loading
```sql
casual_rate = base_rate × (1 + casual_loading_percentage)
```

**Example:**
```
Input: Base $25.00, Casual loading 25%
Calculation: $25.00 × 1.25 = $31.25
```

#### 3. Weekend Penalties
```sql
weekend_rate = casual_rate × penalty_multiplier
```

**Example - Casual Saturday:**
```
Step 1: Base $25.00 × Casual 1.25 = $31.25
Step 2: $31.25 × Saturday 1.5 = $46.88
```

**Example - Casual Sunday:**
```
Step 1: Base $25.00 × Casual 1.25 = $31.25
Step 2: $31.25 × Sunday 2.0 = $62.50
```

#### 4. Junior Rates
```sql
junior_rate = adult_rate × junior_percentage
```

**Example - 18-year-old:**
```
Adult rate: $25.00
Junior percentage (18 years): 70%
Junior rate: $25.00 × 0.70 = $17.50
```

#### 5. Compound Calculations
For junior casual weekend rates, apply in order:

```sql
step1_junior = adult_base × junior_percentage
step2_casual = junior_rate × (1 + casual_loading)
step3_weekend = casual_rate × weekend_penalty
```

**Example - 18-year-old casual Sunday:**
```
Step 1: Base $25.00 × Junior 0.70 = $17.50
Step 2: $17.50 × Casual 1.25 = $21.88
Step 3: $21.88 × Sunday 2.0 = $43.76
```

### Calculation Matrix

For each classification in an award, the system generates rates for:

| Employment Type | Day Types | Shift Types | Age Categories | Total Combinations |
|----------------|-----------|-------------|----------------|-------------------|
| FULL_TIME      | 4 (Weekday, Sat, Sun, Holiday) | 6 (Standard, Night, etc.) | 1 (Adult) | 24 |
| PART_TIME      | 4 | 6 | 1 | 24 |
| CASUAL         | 4 | 6 | 1 | 24 |
| **Subtotal**   | | | | **72 per classification** |

With junior rates (5 age brackets), multiply by 6:
- **432 rates per classification** (if junior rates apply)

For an award with 10 classifications:
- **4,320 total calculated rates**

## API Usage

### 1. Calculate Pay Rates

Trigger the calculation stored procedure:

```bash
# Calculate for specific award
curl -X POST http://localhost:5000/api/calculatedpayrates/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "awardCode": "MA000120"
  }'
```

**Response:**
```json
{
  "status": "Success",
  "totalRecordsCreated": 4320,
  "durationSeconds": 45,
  "awardsProcessed": 1,
  "classificationsProcessed": 10,
  "fullTimeRates": 1440,
  "partTimeRates": 1440,
  "casualRates": 1440,
  "message": "Successfully calculated 4320 pay rates"
}
```

### 2. Query Calculated Rates

Get rates with filtering:

```bash
# Get all casual Sunday rates
curl "http://localhost:5000/api/calculatedpayrates?awardCode=MA000120&employmentType=CASUAL&dayType=SUNDAY&pageSize=100"
```

**Response:**
```json
[
  {
    "id": 12345,
    "awardCode": "MA000120",
    "awardName": "Children's Services Award 2010",
    "classificationName": "Support Worker - Level 1.1",
    "baseRate": 25.00,
    "employmentType": "CASUAL",
    "employeeAgeCategory": "ADULT",
    "dayType": "SUNDAY",
    "shiftType": "STANDARD",
    "casualLoadingApplied": 0.2500,
    "casualLoadedRate": 31.25,
    "penaltyMultiplierApplied": 2.0000,
    "calculatedHourlyRate": 62.50,
    "calculationSteps": "Base: $25.00 × Casual 1.25 = $31.25 × Sunday 2.0 = $62.50",
    "effectiveFrom": "2024-01-01"
  }
]
```

### 3. Filter Examples

**Get night shift rates:**
```bash
curl "http://localhost:5000/api/calculatedpayrates?awardCode=MA000120&shiftType=NIGHT&pageSize=50"
```

**Get junior rates (18-year-olds):**
```bash
curl "http://localhost:5000/api/calculatedpayrates?awardCode=MA000120&employeeAgeCategory=AGE_18&pageSize=50"
```

**Get full-time weekday rates:**
```bash
curl "http://localhost:5000/api/calculatedpayrates?awardCode=MA000120&employmentType=FULL_TIME&dayType=WEEKDAY&pageSize=50"
```

**Get specific classification:**
```bash
curl "http://localhost:5000/api/calculatedpayrates?awardCode=MA000120&classificationFixedId=4591&pageSize=100"
```

### 4. Get Statistics

Summary stats for an award:

```bash
curl "http://localhost:5000/api/calculatedpayrates/statistics?awardCode=MA000120"
```

**Response:**
```json
{
  "totalRates": 4320,
  "byEmploymentType": [
    {"employmentType": "FULL_TIME", "count": 1440},
    {"employmentType": "PART_TIME", "count": 1440},
    {"employmentType": "CASUAL", "count": 1440}
  ],
  "byDayType": [
    {"dayType": "WEEKDAY", "count": 1080},
    {"dayType": "SATURDAY", "count": 1080},
    {"dayType": "SUNDAY", "count": 1080},
    {"dayType": "PUBLIC_HOLIDAY", "count": 1080}
  ],
  "averageRate": 38.25,
  "minRate": 12.50,
  "maxRate": 78.13
}
```

## System Admin UI Integration

### Display Award Pay Rates

**Scenario:** System Admin wants to see all pay scenarios for an award to assign to a tenant.

**API Call:**
```javascript
fetch('http://localhost:5000/api/calculatedpayrates?awardCode=MA000120&pageSize=500')
  .then(res => res.json())
  .then(data => {
    // Display in table or grid
    displayPayRates(data);
  });
```

**UI Table Structure:**
```
Classification | Employment Type | Day Type | Shift Type | Age | Rate | Details
---------------|-----------------|----------|------------|-----|------|--------
Level 1.1      | Full-time      | Weekday  | Standard   | Adult | $24.95 | Base rate
Level 1.1      | Full-time      | Saturday | Standard   | Adult | $37.43 | 150% penalty
Level 1.1      | Full-time      | Sunday   | Standard   | Adult | $49.90 | 200% penalty
Level 1.1      | Casual         | Weekday  | Standard   | Adult | $31.19 | 25% loading
Level 1.1      | Casual         | Sunday   | Standard   | Adult | $62.38 | Casual + Sunday
Level 1.1      | Casual         | Sunday   | Standard   | Age 18 | $43.67 | Junior + Casual + Sunday
```

### Filter UI Controls

**Employment Type Dropdown:**
```jsx
<select onChange={(e) => setEmploymentType(e.target.value)}>
  <option value="">All</option>
  <option value="FULL_TIME">Full-time</option>
  <option value="PART_TIME">Part-time</option>
  <option value="CASUAL">Casual</option>
</select>
```

**Day Type Filter:**
```jsx
<select onChange={(e) => setDayType(e.target.value)}>
  <option value="">All</option>
  <option value="WEEKDAY">Weekday</option>
  <option value="SATURDAY">Saturday</option>
  <option value="SUNDAY">Sunday</option>
  <option value="PUBLIC_HOLIDAY">Public Holiday</option>
</select>
```

**Age Category Filter:**
```jsx
<select onChange={(e) => setAgeCategory(e.target.value)}>
  <option value="">All</option>
  <option value="ADULT">Adult (21+)</option>
  <option value="AGE_20">20 years</option>
  <option value="AGE_19">19 years</option>
  <option value="AGE_18">18 years</option>
  <option value="AGE_17">17 years</option>
  <option value="AGE_16">16 years</option>
  <option value="UNDER_16">Under 16</option>
</select>
```

### Display Calculation Steps

Show how rate was calculated:

```jsx
<td className="calculation-details">
  <Tooltip content={rate.calculationSteps}>
    ${rate.calculatedHourlyRate.toFixed(2)}
  </Tooltip>
</td>
```

**Tooltip Content:**
```
Base: $25.00 × Casual 1.25 = $31.25 × Sunday 2.0 = $62.50
```

## Maintenance & Updates

### Adding New Penalty Rates

When FWC updates penalty rates:

```sql
-- Update existing penalty
UPDATE TblPenaltyRates 
SET penalty_multiplier = 1.6000, 
    effective_to = '2024-12-31'
WHERE award_code = 'MA000120' 
  AND penalty_type = 'SATURDAY';

-- Add new penalty with new effective date
INSERT INTO TblPenaltyRates 
  (award_code, penalty_type, penalty_multiplier, effective_from, clause_reference)
VALUES 
  ('MA000120', 'SATURDAY', 1.7000, '2025-01-01', 'Clause 15.3 - Updated 2025');

-- Recalculate rates
EXEC sp_CalculateAllPayRates @award_code = 'MA000120';
```

### Adding Junior Rates

```sql
INSERT INTO TblJuniorRates 
  (award_code, age_from, age_to, junior_percentage, effective_from, clause_reference)
VALUES 
  ('MA000120', 15, 15, 0.4500, '2024-01-01', 'Clause 12.1 - Junior rates');

-- Recalculate to include new age bracket
EXEC sp_CalculateAllPayRates @award_code = 'MA000120';
```

### Performance Optimization

For large-scale calculations:

**Option 1: Calculate by award**
```sql
-- Instead of all awards at once
EXEC sp_CalculateAllPayRates @award_code = 'MA000120';
EXEC sp_CalculateAllPayRates @award_code = 'MA000002';
```

**Option 2: Calculate by classification**
```sql
EXEC sp_CalculateAllPayRates 
  @award_code = 'MA000120',
  @classification_fixed_id = 4591;
```

**Option 3: Schedule during off-peak hours**
```sql
-- SQL Server Agent Job
-- Run daily at 2 AM to recalculate all rates
EXEC sp_CalculateAllPayRates;
```

## Troubleshooting

### Issue: No rates generated

**Check 1: Reference data exists**
```sql
SELECT COUNT(*) FROM TblPenaltyRates WHERE award_code = 'MA000120';
SELECT COUNT(*) FROM TblCasualLoadings WHERE award_code = 'MA000120';
```

**Check 2: Base rates exist**
```sql
SELECT COUNT(*) FROM Stg_TblPayRates WHERE award_code = 'MA000120' AND base_rate > 0;
```

**Check 3: Stored procedure executed successfully**
```sql
SELECT * FROM TblPayCalculationLog 
WHERE award_code = 'MA000120' 
ORDER BY created_at DESC;
```

### Issue: Incorrect calculations

**Verify multipliers:**
```sql
SELECT * FROM TblPenaltyRates 
WHERE award_code = 'MA000120' 
  AND penalty_type = 'SUNDAY';
-- Should show 2.0000 for 200%
```

**Check calculation steps:**
```sql
SELECT TOP 10
  classification_name,
  employment_type,
  day_type,
  base_rate,
  casual_loading_applied,
  penalty_multiplier_applied,
  calculated_hourly_rate,
  calculation_steps
FROM TblCalculatedPayRates
WHERE award_code = 'MA000120'
  AND employment_type = 'CASUAL'
  AND day_type = 'SUNDAY';
```

## Summary

This pay calculation system provides:

✅ **Complete FWC compliance** - Applies all penalty rates, loadings, and conditions  
✅ **Comprehensive coverage** - 500-2000+ rate combinations per award  
✅ **Transparency** - Stores calculation steps for audit  
✅ **Performance** - Pre-calculated rates for fast lookups  
✅ **Flexibility** - Easy to add new penalties, age brackets, allowances  
✅ **Scalability** - Handles hundreds of awards  
✅ **API-first** - REST endpoints for UI integration  

System Admins can now:
- View ALL possible pay scenarios for any award
- Filter by employment type, day, shift, age
- Understand how rates are calculated
- Assign appropriate rates to tenants
- Provide clear data to QA and Business Analysts
