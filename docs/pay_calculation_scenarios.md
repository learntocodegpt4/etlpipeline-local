# FWC Pay Calculation Scenarios

## Overview

This document outlines all pay calculation scenarios based on Fair Work Commission (FWC) awards. The system must calculate actual pay rates by applying various conditions, penalties, and loadings to base rates.

## Core Concept

**FWC provides rules, not final rates.** The system must:
1. Read base rates from staging tables
2. Apply conditions (time, day type, employment type, age)
3. Calculate final pay rates using FWC-defined multipliers
4. Store all possible combinations for quick lookup

---

## Employment Type Scenarios

### Scenario 1: Full-Time Employee
**Base Calculation:**
- Uses standard base rate from FWC
- No loading applied
- Eligible for overtime penalties

**Example:**
```
Base rate: $25.00/hour
Final rate: $25.00/hour
```

### Scenario 2: Part-Time Employee
**Base Calculation:**
- Uses standard base rate from FWC
- Pro-rata entitlements
- Eligible for overtime penalties (same as full-time)

**Example:**
```
Base rate: $25.00/hour
Final rate: $25.00/hour
```

### Scenario 3: Casual Employee
**Base Calculation:**
- Base rate + casual loading (typically 25%)
- No overtime penalties (casual loading compensates)
- Loading percentage varies by award

**Example:**
```
Base rate: $25.00/hour
Casual loading: 25%
Casual base rate: $25.00 × 1.25 = $31.25/hour
```

**Calculation Rule:**
```
casual_rate = base_rate × (1 + casual_loading_percentage)
```

---

## Time-Based Penalties

### Scenario 4: Weekend Work - Saturday
**FWC Rules (Common):**
- Saturday (before certain time): 150% of base rate
- Saturday (after certain time): 175% or 200% of base rate
- Varies by award and industry

**Example 1 - Retail:**
```
Base rate: $25.00/hour
Saturday rate: $25.00 × 1.5 = $37.50/hour
```

**Example 2 - Hospitality (after 7 PM):**
```
Base rate: $25.00/hour
Saturday after 7 PM: $25.00 × 1.75 = $43.75/hour
```

**Calculation Rule:**
```
saturday_rate = base_rate × saturday_penalty_multiplier
(multiplier varies: 1.5, 1.75, 2.0 depending on time and award)
```

### Scenario 5: Weekend Work - Sunday
**FWC Rules:**
- Sunday rate: typically 175% to 200% of base rate
- Higher penalty than Saturday
- May vary by time of day

**Example:**
```
Base rate: $25.00/hour
Sunday rate: $25.00 × 2.0 = $50.00/hour
```

**Calculation Rule:**
```
sunday_rate = base_rate × sunday_penalty_multiplier
(multiplier typically: 1.75 or 2.0)
```

### Scenario 6: Public Holiday
**FWC Rules:**
- Public holiday rate: typically 200% to 250% of base rate
- Highest penalty rate
- Additional day off in lieu may apply

**Example:**
```
Base rate: $25.00/hour
Public holiday rate: $25.00 × 2.5 = $62.50/hour
```

**Calculation Rule:**
```
public_holiday_rate = base_rate × public_holiday_multiplier
(multiplier typically: 2.0, 2.25, or 2.5)
```

---

## Shift-Based Penalties

### Scenario 7: Night Shift
**FWC Rules:**
- Work after certain time (e.g., 7 PM, 8 PM, or 10 PM)
- Additional percentage or flat allowance
- May combine with other penalties

**Example 1 - Percentage:**
```
Base rate: $25.00/hour
Night shift penalty: 15%
Night shift rate: $25.00 × 1.15 = $28.75/hour
```

**Example 2 - Flat Allowance:**
```
Base rate: $25.00/hour
Night shift allowance: $2.50/hour
Night shift rate: $25.00 + $2.50 = $27.50/hour
```

**Calculation Rule:**
```
IF penalty_type = 'PERCENTAGE':
    night_rate = base_rate × (1 + night_penalty_percentage)
ELSE IF penalty_type = 'FLAT':
    night_rate = base_rate + night_allowance_amount
```

### Scenario 8: Early Morning Shift
**FWC Rules:**
- Work before certain time (e.g., 5 AM or 6 AM)
- Similar to night shift penalties
- Less common than night shift

**Example:**
```
Base rate: $25.00/hour
Early morning penalty: 10%
Early morning rate: $25.00 × 1.10 = $27.50/hour
```

**Calculation Rule:**
```
early_morning_rate = base_rate × (1 + early_morning_penalty_percentage)
```

### Scenario 9: Afternoon Shift
**FWC Rules:**
- Work during afternoon hours (e.g., 2 PM to 10 PM)
- Lower penalty than night shift
- Typically 10-15%

**Example:**
```
Base rate: $25.00/hour
Afternoon shift penalty: 12.5%
Afternoon shift rate: $25.00 × 1.125 = $28.13/hour
```

**Calculation Rule:**
```
afternoon_rate = base_rate × (1 + afternoon_penalty_percentage)
```

---

## Overtime Scenarios

### Scenario 10: Overtime - First 2 Hours
**FWC Rules:**
- First 2 hours after standard shift: 150% of base rate
- Monday to Friday typically
- Not applicable to casuals

**Example:**
```
Base rate: $25.00/hour
Overtime (first 2 hours): $25.00 × 1.5 = $37.50/hour
```

**Calculation Rule:**
```
overtime_first_2hrs_rate = base_rate × 1.5
```

### Scenario 11: Overtime - After 2 Hours
**FWC Rules:**
- After first 2 hours: 200% of base rate
- Higher penalty for extended hours
- Not applicable to casuals

**Example:**
```
Base rate: $25.00/hour
Overtime (after 2 hours): $25.00 × 2.0 = $50.00/hour
```

**Calculation Rule:**
```
overtime_after_2hrs_rate = base_rate × 2.0
```

### Scenario 12: Weekend Overtime
**FWC Rules:**
- Overtime on Saturday: weekend penalty OR overtime penalty (whichever is higher)
- Overtime on Sunday: similar rules
- Complex calculation

**Example:**
```
Base rate: $25.00/hour
Saturday penalty: 150% = $37.50
Overtime penalty: 150% = $37.50
Applied: $37.50 (same in this case)

OR

Saturday penalty: 200% = $50.00
Overtime penalty: 150% = $37.50
Applied: $50.00 (higher penalty)
```

**Calculation Rule:**
```
weekend_overtime_rate = MAX(weekend_penalty_rate, overtime_penalty_rate)
```

---

## Combined Scenarios

### Scenario 13: Casual + Weekend
**FWC Rules:**
- Apply casual loading to base rate first
- Then apply weekend penalty to casual base rate
- Compound calculation

**Example:**
```
Base rate: $25.00/hour
Casual loading: 25%
Casual base: $25.00 × 1.25 = $31.25/hour

Sunday penalty: 150%
Final rate: $31.25 × 1.5 = $46.88/hour
```

**Calculation Rule:**
```
step1_casual_base = base_rate × (1 + casual_loading)
step2_final_rate = casual_base × weekend_penalty_multiplier
```

### Scenario 14: Casual + Public Holiday
**FWC Rules:**
- Apply casual loading first
- Then apply public holiday penalty
- Results in very high rates

**Example:**
```
Base rate: $25.00/hour
Casual loading: 25%
Casual base: $25.00 × 1.25 = $31.25/hour

Public holiday penalty: 250%
Final rate: $31.25 × 2.5 = $78.13/hour
```

**Calculation Rule:**
```
step1_casual_base = base_rate × (1 + casual_loading)
step2_final_rate = casual_base × public_holiday_multiplier
```

### Scenario 15: Night Shift + Weekend
**FWC Rules:**
- Typically the higher penalty applies
- Or penalties may be additive (depends on award)
- Check specific award rules

**Example 1 - Higher Penalty:**
```
Base rate: $25.00/hour
Night penalty: 15% = $28.75
Saturday penalty: 150% = $37.50
Applied: $37.50 (higher)
```

**Example 2 - Additive:**
```
Base rate: $25.00/hour
Night penalty: 15%
Saturday penalty: 50%
Combined: $25.00 × (1 + 0.15 + 0.50) = $25.00 × 1.65 = $41.25
```

**Calculation Rule:**
```
IF award_rule = 'HIGHER':
    rate = MAX(night_shift_rate, weekend_rate)
ELSE IF award_rule = 'ADDITIVE':
    rate = base_rate × (1 + night_penalty + weekend_penalty)
```

---

## Age-Based Rates (Junior Employees)

### Scenario 16: Junior Employee Rates
**FWC Rules:**
- Employees under 21 typically paid percentage of adult rate
- Percentage increases with age
- Common scale: 16 years = 50%, 20 years = 90%

**Example:**
```
Adult base rate: $25.00/hour
Employee age: 18 years
Junior percentage: 70% (for 18-year-old)
Junior rate: $25.00 × 0.70 = $17.50/hour
```

**Common Junior Rate Table:**
| Age | Percentage of Adult Rate |
|-----|--------------------------|
| Under 16 | 40-45% |
| 16 years | 50-55% |
| 17 years | 60-65% |
| 18 years | 70-75% |
| 19 years | 80-85% |
| 20 years | 90-95% |
| 21+ years | 100% (Adult) |

**Calculation Rule:**
```
junior_rate = adult_base_rate × junior_percentage_for_age
```

### Scenario 17: Junior + Casual
**FWC Rules:**
- Apply junior percentage first
- Then apply casual loading
- Compound calculation

**Example:**
```
Adult base rate: $25.00/hour
Junior percentage (age 18): 70%
Junior base: $25.00 × 0.70 = $17.50/hour

Casual loading: 25%
Final rate: $17.50 × 1.25 = $21.88/hour
```

**Calculation Rule:**
```
step1_junior_base = adult_base_rate × junior_percentage
step2_final_rate = junior_base × (1 + casual_loading)
```

### Scenario 18: Junior + Weekend
**FWC Rules:**
- Apply junior percentage first
- Then apply weekend penalty
- Compound calculation

**Example:**
```
Adult base rate: $25.00/hour
Junior percentage (age 18): 70%
Junior base: $25.00 × 0.70 = $17.50/hour

Saturday penalty: 150%
Final rate: $17.50 × 1.5 = $26.25/hour
```

**Calculation Rule:**
```
step1_junior_base = adult_base_rate × junior_percentage
step2_final_rate = junior_base × weekend_penalty_multiplier
```

---

## Allowances

### Scenario 19: Meal Allowance (Conditional)
**FWC Rules:**
- If shift exceeds X hours, OR
- If shift ends after certain time (e.g., 9 PM)
- Flat rate allowance added

**Example:**
```
Base pay: $25.00/hour × 8 hours = $200.00
Shift ends at 10 PM (after 9 PM threshold)
Meal allowance: $15.00
Total: $200.00 + $15.00 = $215.00
```

**Condition Logic:**
```
IF shift_end_time > threshold_time OR shift_duration > threshold_hours:
    add_meal_allowance = TRUE
```

**Calculation Rule:**
```
total_pay = (hourly_rate × hours_worked) + meal_allowance
```

### Scenario 20: Uniform/Laundry Allowance
**FWC Rules:**
- Per shift or per day allowance
- Applied if uniform required
- Added to total pay

**Example:**
```
Daily pay: $200.00
Laundry allowance: $1.50/day
Total: $200.00 + $1.50 = $201.50
```

**Calculation Rule:**
```
total_pay = base_pay + laundry_allowance_per_day
```

### Scenario 21: Tool/Equipment Allowance
**FWC Rules:**
- Per week or per shift allowance
- If employee provides own tools
- Added to total pay

**Example:**
```
Weekly pay: $1,000.00
Tool allowance: $25.00/week
Total: $1,000.00 + $25.00 = $1,025.00
```

**Calculation Rule:**
```
total_pay = base_pay + tool_allowance_per_week
```

---

## Apprentice and Trainee Rates

### Scenario 22: Apprentice Rates
**FWC Rules:**
- Percentage of qualified rate
- Increases with year of apprenticeship
- Common: Year 1 = 55%, Year 2 = 65%, Year 3 = 80%, Year 4 = 95%

**Example:**
```
Qualified tradesperson rate: $30.00/hour
Apprentice year: 2nd year
Apprentice percentage: 65%
Apprentice rate: $30.00 × 0.65 = $19.50/hour
```

**Calculation Rule:**
```
apprentice_rate = qualified_rate × apprentice_year_percentage
```

### Scenario 23: Trainee Rates
**FWC Rules:**
- Similar to apprentice structure
- May have different percentages
- Based on qualification level

**Example:**
```
Qualified worker rate: $25.00/hour
Trainee level: Certificate III (Year 1)
Trainee percentage: 60%
Trainee rate: $25.00 × 0.60 = $15.00/hour
```

**Calculation Rule:**
```
trainee_rate = qualified_rate × trainee_level_percentage
```

---

## Special Industry Scenarios

### Scenario 24: Split Shift
**FWC Rules:**
- Employee works two separate periods in one day
- Allowance for split shift inconvenience
- Flat rate per occurrence

**Example:**
```
Shift 1: 6 AM - 10 AM (4 hours × $25.00) = $100.00
Shift 2: 5 PM - 9 PM (4 hours × $25.00) = $100.00
Split shift allowance: $8.50
Total: $100.00 + $100.00 + $8.50 = $208.50
```

**Calculation Rule:**
```
total_pay = (hours_shift1 × rate) + (hours_shift2 × rate) + split_shift_allowance
```

### Scenario 25: Sleepover Shift (Community Services)
**FWC Rules:**
- Flat rate for sleepover duty
- Additional hourly rate if called to work
- Common in disability and aged care

**Example:**
```
Sleepover shift: $80.00 (flat rate for 8 hours)
Called to work: 2 hours × $25.00 = $50.00
Total: $80.00 + $50.00 = $130.00
```

**Calculation Rule:**
```
total_pay = sleepover_flat_rate + (active_hours × hourly_rate)
```

### Scenario 26: On-Call Allowance
**FWC Rules:**
- Lower rate for being on-call
- Higher rate if called to work
- Minimum engagement period applies

**Example:**
```
On-call (8 hours): $5.00/hour × 8 = $40.00
Called to work: 3 hours × $25.00 × 1.5 (overtime) = $112.50
Total: $40.00 + $112.50 = $152.50
```

**Calculation Rule:**
```
total_pay = (oncall_hours × oncall_rate) + (worked_hours × overtime_rate)
```

---

## Calculation Priority and Hierarchy

### Order of Operations
When multiple conditions apply, calculations must follow this order:

1. **Base Rate Selection**
   - Adult rate OR Junior rate OR Apprentice rate

2. **Employment Type Loading**
   - Full-time/Part-time: no loading
   - Casual: apply casual loading

3. **Time-Based Penalties**
   - Apply highest applicable penalty:
     - Public Holiday (highest)
     - Sunday
     - Saturday
     - Night shift
     - Afternoon shift
     - Early morning shift

4. **Overtime Penalties**
   - Compare with time-based penalty
   - Apply higher rate

5. **Allowances**
   - Add all applicable allowances
   - Meal, uniform, tools, etc.

### Example - Complex Calculation
```
Employee: 19-year-old casual
Day: Sunday
Time: 8 PM - 12 AM (4 hours, includes night shift)
Award: Retail Award

Step 1: Base rate (adult) = $23.50/hour
Step 2: Junior rate (19 years, 85%) = $23.50 × 0.85 = $19.98/hour
Step 3: Casual loading (25%) = $19.98 × 1.25 = $24.98/hour
Step 4: Sunday penalty (200%) = $24.98 × 2.0 = $49.96/hour
        Night penalty (115%) = $24.98 × 1.15 = $28.73/hour
        Apply higher: $49.96/hour
Step 5: Total = $49.96 × 4 hours = $199.84
```

---

## Data Requirements

### Penalty Rate Reference Table
The system needs a reference table storing:
- Award code
- Penalty type (SATURDAY, SUNDAY, PUBLIC_HOLIDAY, NIGHT, etc.)
- Penalty multiplier or flat amount
- Time conditions (start_time, end_time)
- Effective date range

### Junior Rate Reference Table
- Award code
- Age bracket
- Percentage of adult rate
- Effective date range

### Casual Loading Reference Table
- Award code
- Casual loading percentage
- Effective date range

### Allowance Conditions Table
- Award code
- Allowance type
- Condition type (TIME_BASED, SHIFT_LENGTH, etc.)
- Condition value (time threshold, hour threshold)
- Allowance amount
- Effective date range

---

## Implementation Strategy

### Phase 1: Core Penalties
1. Weekend rates (Saturday, Sunday)
2. Public holiday rates
3. Casual loading
4. Junior rates

### Phase 2: Shift Penalties
1. Night shift
2. Afternoon shift
3. Early morning shift
4. Overtime (first 2 hours, after 2 hours)

### Phase 3: Conditional Allowances
1. Meal allowances
2. Uniform/laundry allowances
3. Tool allowances

### Phase 4: Special Cases
1. Apprentice/trainee rates
2. Split shift
3. On-call
4. Sleepover

### Phase 5: Complex Combinations
1. Junior + Casual + Weekend
2. Casual + Public Holiday + Night
3. All possible valid combinations

---

## Validation Rules

1. **Casual employees cannot receive overtime penalties** (casual loading compensates)
2. **Weekend penalty and overtime penalty**: apply higher rate, not both
3. **Age-based rates**: verify employee age matches bracket
4. **Allowances**: verify conditions are met before applying
5. **Minimum engagement**: ensure minimum hours paid (e.g., 3-hour minimum)
6. **Break deductions**: unpaid breaks must be subtracted from hours
7. **Public holiday working**: some awards require both penalty pay AND day in lieu

---

## Summary

The system must generate a **comprehensive pay rate matrix** for each award containing:
- Every classification level
- Every employment type (Full-time, Part-time, Casual)
- Every age bracket (Adult, 20, 19, 18, 17, 16, Under 16)
- Every penalty scenario (Saturday, Sunday, Public Holiday, Night, Overtime, etc.)
- All applicable allowances

This enables the UI to:
1. Show System Admin all possible pay scenarios
2. Filter by conditions (age, employment type, day type, shift type)
3. Assign appropriate rates to employees
4. Calculate correct pay for any given shift

Total possible combinations per award: **500-2000+ records** depending on complexity.
