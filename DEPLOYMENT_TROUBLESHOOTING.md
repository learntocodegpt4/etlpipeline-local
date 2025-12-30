# Deployment Troubleshooting Guide

## Issue 1: Penalties Not Loading in Docker Deployment

### Problem
When triggering ETL jobs from the UI on Docker deployment, penalties data fails to load with errors:
- `Invalid column name 'penalty_code'`
- `Invalid column name 'penalty_rate'`
- Multiple TCP connection failures

### Root Cause
The penalties transformer was using old field names that don't match the database schema:
- Old: `penalty_code`, `penalty_rate`, `classification_fixed_id`
- New: (removed `penalty_code`), `rate`, `classification_level`

### Solution

#### Option 1: Rebuild Docker Containers (Recommended)
```bash
cd /Users/amreekbasra/SourceCode/UI/etlpipeline-local

# Stop and rebuild API container to clear Python cache
docker compose -f docker/docker-compose.yml down api
docker compose -f docker/docker-compose.yml build --no-cache api
docker compose -f docker/docker-compose.yml up -d api
```

#### Option 2: Restart API Container
If volumes are properly mounted, simply restart to reload Python modules:
```bash
docker compose -f docker/docker-compose.yml restart api
```

#### Option 3: Clear Python Cache Inside Container
```bash
# Access the running container
docker compose -f docker/docker-compose.yml exec api bash

# Clear all Python cache
find /app -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find /app -type f -name "*.pyc" -delete

# Exit and restart
exit
docker compose -f docker/docker-compose.yml restart api
```

### Verification
After fixing, verify the transformer is using correct fields:
```bash
# Check the transformer code in container
docker compose -f docker/docker-compose.yml exec api cat src/transform/transformers/penalties.py | grep -A 5 "transform_record"

# Should see: "rate", "classification_level" (NOT "penalty_code" or "penalty_rate")
```

---

## Issue 2: Triggering Jobs for Specific Awards from UI

### Feature Added
Enhanced the UI trigger dialog to support:
1. **All Awards Mode** (default): Loads all 150+ active awards
2. **Specific Awards Mode**: Load data for one or more specific awards

### How to Use

#### From UI (http://your-ip:8081/etlui/jobs)
1. Click "Trigger Job" button
2. Choose your mode:
   - **All Awards**: Keep "Load all active awards" checkbox checked
   - **Specific Awards**: Uncheck the box and enter award codes

3. For specific awards, enter codes in the text field:
   - Single award: `MA000120`
   - Multiple awards: `MA000120, MA000004, MA000029`

4. Click "Trigger Job"

#### From API (curl)
```bash
# Trigger for all awards
curl -X POST "http://your-ip:8081/etlapi/api/jobs/trigger" \
  -H "Content-Type: application/json" \
  -d '{}'

# Trigger for specific award
curl -X POST "http://your-ip:8081/etlapi/api/jobs/trigger" \
  -H "Content-Type: application/json" \
  -d '{"award_codes": ["MA000120"]}'

# Trigger for multiple awards
curl -X POST "http://your-ip:8081/etlapi/api/jobs/trigger" \
  -H "Content-Type: application/json" \
  -d '{"award_codes": ["MA000120", "MA000004", "MA000029"]}'
```

### What Gets Loaded
The ETL pipeline loads **ALL staging tables** for the specified awards:
- `Stg_TblAwardsDetailed`
- `Stg_TblClassifications`
- `Stg_TblPayRates`
- `Stg_TblWageAllowances`
- `Stg_TblExpenseAllowances`
- `Stg_TblPenalties`

Example: Triggering MA000120 will:
1. Extract all data from FWC API for MA000120
2. Transform and load into all 6 staging tables
3. Show job progress in UI

---

## Database Schema Verification

### Check Stg_TblPenalties Schema
```sql
-- Run in SQL Server Management Studio or Azure Data Studio
SELECT 
    COLUMN_NAME,
    DATA_TYPE,
    CHARACTER_MAXIMUM_LENGTH,
    IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'Stg_TblPenalties'
ORDER BY ORDINAL_POSITION;
```

Expected columns:
- `penalty_fixed_id` (INT)
- `award_code` (NVARCHAR(50))
- `rate` (DECIMAL(18,2)) ← NOT penalty_rate
- `classification_level` (INT) ← NOT penalty_code
- `penalty_description` (NVARCHAR(1000))
- `employee_rate_type_code` (NVARCHAR(20))
- `penalty_calculated_value` (DECIMAL(18,4))
- `calculated_includes_all_purpose` (BIT)
- `base_pay_rate_id` (NVARCHAR(50))
- `clause_fixed_id`, `clause_description`
- `operative_from`, `operative_to`
- `version_number`, `last_modified_datetime`, `published_year`

---

## Common Issues and Solutions

### Issue: "Invalid column name 'penalty_code'"
**Cause**: Old transformer code cached in Python  
**Solution**: Rebuild Docker container or clear Python cache

### Issue: "TCP Provider: Error code 0x2714"
**Cause**: Too many concurrent connections to SQL Server  
**Solution**: Already fixed - batch_size reduced to 200, retry logic added

### Issue: Jobs trigger but no data loads
**Cause**: Award may have no penalties in FWC API (e.g., MA000120)  
**Solution**: Test with awards known to have data:
- MA000004: 7,652 penalties
- MA000029: 5,154 penalties
- MA000001: 7,700 penalties

### Issue: UI not reflecting code changes
**Cause**: Next.js build cache  
**Solution**: Rebuild UI container:
```bash
docker compose -f docker/docker-compose.yml down ui
docker compose -f docker/docker-compose.yml build --no-cache ui
docker compose -f docker/docker-compose.yml up -d ui
```

---

## Performance Notes

### Estimated Load Times (Based on MA000004 benchmark)
- **Single Award** (7,652 penalties):
  - Extraction: ~2.5 minutes
  - Transformation: <1 second
  - Loading: ~30-40 minutes
  - **Total: ~35-45 minutes**

- **All Awards** (~150 awards, ~50,000+ penalties):
  - Extraction: ~10-15 minutes
  - Transformation: ~5 seconds
  - Loading: ~8-10 hours
  - **Total: ~8-10 hours**

### Optimization Tips
1. Use specific awards for testing/debugging
2. Schedule all-awards jobs during off-peak hours
3. Monitor job progress via UI at `/etlui/jobs/{job_id}`
4. Check diagnostics endpoint: `/etlapi/api/jobs/{job_id}/diagnostics`

---

## Files Modified

### UI Changes
- `ui/src/app/jobs/page.tsx`: Added award code input dialog
- `ui/src/lib/api.ts`: Already supports award_codes parameter

### Backend Changes
- `src/transform/transformers/penalties.py`: Fixed field names
- `src/load/bulk_loader.py`: Added retry logic, reduced batch size

### Database
- `migrations/sql/010_create_penalties_staging_table.sql`: Defines correct schema
