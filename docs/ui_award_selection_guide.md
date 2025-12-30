# UI Enhancement: Award Code Selection Guide

## New Feature: Trigger Jobs for Specific Awards

### Visual Guide

#### Before (Old Dialog)
```
┌─────────────────────────────────────────┐
│  Trigger ETL Pipeline                   │
├─────────────────────────────────────────┤
│                                         │
│  Are you sure you want to manually     │
│  trigger the ETL pipeline? This will   │
│  extract data from the FWC API and     │
│  load it into the database.            │
│                                         │
│           [Cancel]  [Trigger]           │
└─────────────────────────────────────────┘
```

#### After (New Enhanced Dialog)
```
┌─────────────────────────────────────────────────────┐
│  Trigger ETL Pipeline                               │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Configure the ETL job to extract and load data    │
│  from the FWC API.                                 │
│                                                     │
│  ☑ Load all active awards                          │
│                                                     │
│  ┌─────────────────────────────────────────────┐   │
│  │ Award Codes                                 │   │
│  │                                             │   │
│  │ e.g., MA000120, MA000004, MA000029         │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  Example: MA000120 for a single award, or          │
│  MA000120, MA000004, MA000029 for multiple awards  │
│                                                     │
│                    [Cancel]  [Trigger Job]          │
└─────────────────────────────────────────────────────┘
```

---

## Usage Scenarios

### Scenario 1: Load All Awards (Production Full Sync)
**Use Case**: Nightly sync of all FWC Modern Awards  
**Steps**:
1. Click "Trigger Job"
2. Keep ☑ "Load all active awards" checked
3. Click "Trigger Job"

**Result**: 
- Processes ~150+ awards
- Loads all 6 staging tables for each award
- Estimated time: 8-10 hours

---

### Scenario 2: Load Single Award (Testing/Debugging)
**Use Case**: Testing penalties for MA000120  
**Steps**:
1. Click "Trigger Job"
2. Uncheck ☐ "Load all active awards"
3. Enter: `MA000120`
4. Click "Trigger Job"

**Result**:
- Processes only MA000120
- Loads all 6 staging tables for this award
- Estimated time: 5-10 minutes (depending on data volume)

---

### Scenario 3: Load Multiple Specific Awards
**Use Case**: Refresh data for 3 frequently accessed awards  
**Steps**:
1. Click "Trigger Job"
2. Uncheck ☐ "Load all active awards"
3. Enter: `MA000004, MA000029, MA000001`
4. Click "Trigger Job"

**Result**:
- Processes 3 awards sequentially
- Loads ~20,806 total penalties (7,652 + 5,154 + 7,700)
- Estimated time: 1.5-2 hours

---

## What Gets Loaded for Each Award

When you trigger a job for specific award(s), the ETL pipeline extracts and loads:

### Staging Tables Populated:
1. **Stg_TblAwardsDetailed** - Award master data
2. **Stg_TblClassifications** - Job classifications (e.g., Level 1, Level 2)
3. **Stg_TblPayRates** - Base pay rates per classification
4. **Stg_TblWageAllowances** - Additional wage allowances
5. **Stg_TblExpenseAllowances** - Expense reimbursements
6. **Stg_TblPenalties** - Penalty rates (overtime, weekends, public holidays)

### Pipeline Steps:
```
Award(s) Input
    ↓
┌─────────────────────┐
│ 1. Extract          │ → Fetch from FWC API (https://api.fwc.gov.au)
├─────────────────────┤
│ 2. Transform        │ → Map to database schema
├─────────────────────┤
│ 3. Load             │ → Bulk insert/upsert to SQL Server
└─────────────────────┘
    ↓
Data in Staging Tables
```

---

## Monitoring Job Progress

### In the UI

#### Jobs List Page (`/etlui/jobs`)
- **Job Name**: Shows `fwc_awards_etl:MA000120:timestamp` or `fwc_awards_etl:all:timestamp`
- **Status**: pending → running → completed/failed
- **Records**: Total records processed
- **Duration**: Real-time execution time

#### Job Details Page (`/etlui/jobs/{job_id}`)
Click on any Job ID to see:
- **Step-by-step progress**:
  - awards_extractor (1 record)
  - penalties_extractor (e.g., 7,652 records)
  - penalties_transformer (e.g., 7,652 records)
  - Stg_TblPenalties_loader (e.g., 7,652 records)
- **Errors/Warnings** per step
- **Execution times** per step

---

## Input Validation

### Valid Formats
```
✅ MA000120
✅ MA000004, MA000029
✅ MA000001,MA000004,MA000029
✅ ma000120  (auto-uppercased)
```

### Invalid Formats
```
❌ (empty when "Load all active awards" unchecked)
❌ ABC123  (invalid award code format)
```

### Auto-Processing
- **Whitespace**: Automatically trimmed
- **Case**: Automatically uppercased (ma000120 → MA000120)
- **Duplicates**: Not automatically removed (but won't cause errors)

---

## API Payload Examples

When you trigger from UI, it sends:

### All Awards
```json
POST /etlapi/api/jobs/trigger
Content-Type: application/json

{}
```
*Empty body or omitted `award_codes` = process all awards*

### Single Award
```json
POST /etlapi/api/jobs/trigger
Content-Type: application/json

{
  "award_codes": ["MA000120"]
}
```

### Multiple Awards
```json
POST /etlapi/api/jobs/trigger
Content-Type: application/json

{
  "award_codes": ["MA000004", "MA000029", "MA000001"]
}
```

---

## Response Format

### Success Response
```json
{
  "job_id": "be1fd9c7-17c1-4930-89b2-cef9cd07e070",
  "message": "ETL pipeline triggered successfully"
}
```

### Error Response
```json
{
  "detail": "Failed to trigger job"
}
```

---

## Best Practices

### 🎯 For Testing
- Start with a single award that has data: `MA000004`
- Monitor the job details page for step-by-step progress
- Check logs if any step fails

### 🎯 For Production
- Schedule all-awards jobs during off-peak hours (overnight)
- Use specific award codes for urgent data refreshes
- Monitor job completion via UI or API

### 🎯 For Debugging
- Trigger single award to isolate issues
- Check job diagnostics endpoint: `/etlapi/api/jobs/{job_id}/diagnostics`
- Review step-level errors in job details

### 🎯 For Performance
- Batch multiple awards together rather than triggering separately
- The pipeline processes awards sequentially within the same job
- Reduces overall overhead vs. multiple concurrent jobs

---

## Troubleshooting

### Issue: Input field not visible
**Cause**: "Load all active awards" checkbox is checked  
**Solution**: Uncheck the checkbox to reveal the input field

### Issue: "Please enter at least one award code"
**Cause**: Input field is empty when checkbox unchecked  
**Solution**: Either enter award codes or check "Load all active awards"

### Issue: Job triggered but no data loads
**Cause**: Award code may be invalid or have no data  
**Solution**: Verify award code exists in FWC API, test with MA000004

### Issue: Job shows errors for specific table
**Cause**: Could be schema mismatch or data transformation issue  
**Solution**: Check job diagnostics and error messages

---

## Implementation Details

### Files Modified
- **ui/src/app/jobs/page.tsx**: Added state variables and dialog fields
  - `awardCodesInput`: Stores user input
  - `triggerAllAwards`: Boolean checkbox state
  - Enhanced `handleTrigger()`: Parses and validates input

### Backend (No Changes Required)
- **src/api/routes/jobs.py**: Already accepts `award_codes` in `TriggerRequest`
- **src/orchestrator/pipeline.py**: Already filters extractors by award codes
- **src/extract/extractors/*.py**: All extractors support award code filtering

---

## Award Code Reference

### Popular Awards with Penalties Data
| Code | Name | Penalties |
|------|------|-----------|
| MA000004 | Manufacturing Award | 7,652 |
| MA000029 | Hospitality Award | 5,154 |
| MA000001 | Black Coal Mining Award | 7,700 |
| MA000020 | Fast Food Industry Award | ~3,000 |
| MA000003 | Building Award | ~5,000 |

### Test Cases
| Code | Purpose | Expected Result |
|------|---------|-----------------|
| MA000120 | Zero penalties test | Completes quickly, 0 penalties loaded |
| MA000004 | Standard test | ~35 min, 7,652 penalties loaded |
| MA000999 | Invalid code test | Extraction fails, no data |

---

## Future Enhancements (Potential)

1. **Award Code Autocomplete**: Dropdown with valid award codes
2. **Preset Award Groups**: "Healthcare Awards", "Retail Awards", etc.
3. **Schedule Jobs**: Trigger at specific date/time
4. **Batch Size Control**: UI option to adjust batch sizes
5. **Email Notifications**: Alert when long-running jobs complete
6. **Job Templates**: Save common award code combinations

---

## Support

For issues or questions:
1. Check job diagnostics: `/etlapi/api/jobs/{job_id}/diagnostics`
2. Review logs: `docker compose -f docker/docker-compose.yml logs api -f`
3. Check documentation: `DEPLOYMENT_TROUBLESHOOTING.md`
4. Verify database schema matches transformer output
