# Quick Start: Docker Deployment Fix

## Problem Summary
1. **Penalties transformer using old field names** causing "Invalid column name 'penalty_code'" errors
2. **No UI option to trigger jobs for specific awards**

## Solutions Implemented

### ✅ 1. UI Enhancement - Award Code Selection
**File Modified**: `ui/src/app/jobs/page.tsx`

**New Feature**: Trigger dialog now supports:
- **All Awards Mode** (default): Checkbox "Load all active awards"
- **Specific Awards Mode**: Text input for comma-separated award codes

**Usage Example**:
```
Single award:    MA000120
Multiple awards: MA000120, MA000004, MA000029
```

### ✅ 2. Backend Already Supports Award Filtering
**No changes needed** - The API already accepts `award_codes` parameter:
- File: `src/api/routes/jobs.py` - `TriggerRequest` model
- File: `src/orchestrator/pipeline.py` - `ETLPipeline.__init__`

### ✅ 3. Transformer Fix Already Applied
**File**: `src/transform/transformers/penalties.py`

**Correct Fields** (already in code):
```python
"rate": self.to_float(record.get("rate", record.get("penalty_rate")))
"classification_level": self.to_int(record.get("classification_level", record.get("classification_fixed_id")))
# NO "penalty_code" field
```

---

## Docker Deployment Fix Steps

### Step 1: Rebuild API Container (Required)
```bash
cd /Users/amreekbasra/SourceCode/UI/etlpipeline-local

# Stop and remove API container
docker compose -f docker/docker-compose.yml down api

# Rebuild without cache to clear Python bytecode
docker compose -f docker/docker-compose.yml build --no-cache api

# Start API container
docker compose -f docker/docker-compose.yml up -d api
```

### Step 2: Rebuild UI Container (Required for new trigger dialog)
```bash
# Stop and remove UI container
docker compose -f docker/docker-compose.yml down ui

# Rebuild UI
docker compose -f docker/docker-compose.yml build --no-cache ui

# Start UI container
docker compose -f docker/docker-compose.yml up -d ui
```

### Step 3: Verify Services
```bash
# Check all containers are running
docker compose -f docker/docker-compose.yml ps

# Check API logs
docker compose -f docker/docker-compose.yml logs api --tail=50

# Check UI logs
docker compose -f docker/docker-compose.yml logs ui --tail=50
```

### Step 4: Test the Fix

#### Test 1: Access UI
```
URL: http://your-ip:8081/etlui/jobs
```

#### Test 2: Trigger Job for Single Award
1. Click "Trigger Job" button
2. Uncheck "Load all active awards"
3. Enter: `MA000004`
4. Click "Trigger Job"
5. Monitor progress in jobs table

#### Test 3: Verify No Schema Errors
Check job details - should NOT see:
- ❌ "Invalid column name 'penalty_code'"
- ❌ "Invalid column name 'penalty_rate'"

Should see:
- ✅ Steps completing: penalties_extractor, penalties_transformer, Stg_TblPenalties_loader
- ✅ Records processed: ~7,652 for MA000004

---

## API Endpoints Reference

### Trigger All Awards
```bash
curl -X POST "http://your-ip:8081/etlapi/api/jobs/trigger" \
  -H "Content-Type: application/json" \
  -d '{}'
```

### Trigger Single Award
```bash
curl -X POST "http://your-ip:8081/etlapi/api/jobs/trigger" \
  -H "Content-Type: application/json" \
  -d '{"award_codes": ["MA000120"]}'
```

### Trigger Multiple Awards
```bash
curl -X POST "http://your-ip:8081/etlapi/api/jobs/trigger" \
  -H "Content-Type: application/json" \
  -d '{"award_codes": ["MA000004", "MA000029", "MA000001"]}'
```

### Check Job Status
```bash
curl "http://your-ip:8081/etlapi/api/jobs/{job_id}" | jq
```

### Get Job Diagnostics
```bash
curl "http://your-ip:8081/etlapi/api/jobs/{job_id}/diagnostics" | jq
```

---

## Recommended Test Awards

### Awards with Known Penalties Data
| Award Code | Penalties Count | Estimated Load Time |
|------------|-----------------|---------------------|
| MA000004   | 7,652           | ~35-40 minutes      |
| MA000029   | 5,154           | ~25-30 minutes      |
| MA000001   | 7,700           | ~35-40 minutes      |

### Award with No Penalties (for testing)
| Award Code | Penalties Count | Note |
|------------|-----------------|------|
| MA000120   | 0               | Will complete quickly but load 0 penalties |

---

## Troubleshooting

### Issue: Still seeing "penalty_code" errors after rebuild
**Solution**: Clear Python cache manually
```bash
docker compose -f docker/docker-compose.yml exec api bash
find /app -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find /app -type f -name "*.pyc" -delete
exit
docker compose -f docker/docker-compose.yml restart api
```

### Issue: UI not showing new trigger dialog
**Solution**: Clear browser cache or hard refresh
- Chrome/Edge: `Ctrl+Shift+R` (Windows) or `Cmd+Shift+R` (Mac)
- Firefox: `Ctrl+F5` or `Cmd+Shift+R`

### Issue: Container fails to start
**Solution**: Check logs and environment variables
```bash
docker compose -f docker/docker-compose.yml logs api
docker compose -f docker/docker-compose.yml logs ui

# Verify MSSQL_PASSWORD is set
docker compose -f docker/docker-compose.yml exec api env | grep MSSQL
```

### Issue: Cannot connect to SQL Server from Docker
**Solution**: Verify host.docker.internal resolves
```bash
docker compose -f docker/docker-compose.yml exec api ping -c 3 host.docker.internal
```

---

## Complete Rebuild (Nuclear Option)

If issues persist, completely rebuild everything:

```bash
cd /Users/amreekbasra/SourceCode/UI/etlpipeline-local

# Stop and remove all containers
docker compose -f docker/docker-compose.yml down

# Remove volumes (CAUTION: This deletes SQLite state database)
docker compose -f docker/docker-compose.yml down -v

# Rebuild all without cache
docker compose -f docker/docker-compose.yml build --no-cache

# Start all services
docker compose -f docker/docker-compose.yml up -d

# Watch logs
docker compose -f docker/docker-compose.yml logs -f
```

---

## Post-Deployment Verification Checklist

- [ ] API container running: `docker compose -f docker/docker-compose.yml ps`
- [ ] UI container running: `docker compose -f docker/docker-compose.yml ps`
- [ ] API accessible: `curl http://your-ip:8081/etlapi/api/status`
- [ ] UI accessible: Browse to `http://your-ip:8081/etlui`
- [ ] Trigger dialog shows award code input field
- [ ] Test job for MA000004 completes without schema errors
- [ ] Penalties data visible in `/etlui/penalties` page

---

## Next Steps After Deployment

1. **Test Single Award Load**: MA000004 (~35 minutes)
2. **Verify Data**: Check penalties in UI
3. **Monitor Performance**: Watch job diagnostics
4. **Schedule All-Awards Job**: During off-peak hours (8-10 hours)
5. **Set Up Monitoring**: Consider job status alerts

---

## Files Changed in This Update

### UI Changes
- ✅ `ui/src/app/jobs/page.tsx` - Enhanced trigger dialog with award code input

### Backend (Already Fixed)
- ✅ `src/transform/transformers/penalties.py` - Correct field names
- ✅ `src/api/routes/jobs.py` - Already supports award_codes
- ✅ `src/orchestrator/pipeline.py` - Already supports award filtering

### Documentation Added
- ✅ `DEPLOYMENT_TROUBLESHOOTING.md` - Comprehensive troubleshooting guide
- ✅ `DOCKER_DEPLOYMENT_FIX.md` - This quick start guide
