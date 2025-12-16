# Penalties Integration Guide

## Overview

This document describes the integration of FWC Penalties data into the ETL pipeline and Rule Engine system.

## FWC Penalties API

**Endpoint**: `https://api.fwc.gov.au/api/v1/awards/{award_code}/penalties`

**Authentication**: Requires `Ocp-Apim-Subscription-Key` header

**Pagination**: Supports `page` and `limit` parameters (default: 100 records per page)

### Sample Request

```bash
curl 'https://api.fwc.gov.au/api/v1/awards/MA000120/penalties?page=1&limit=100' \
  --header 'Ocp-Apim-Subscription-Key: YOUR_API_KEY' \
  --header 'Accept: application/json' \
  --header 'Cache-Control: no-cache'
```

### Sample Response

```json
{
    "_meta": {
        "current_page": 1,
        "page_count": 77,
        "limit": 100,
        "result_count": 7700,
        "first_row_on_page": 1,
        "last_row_on_page": 100,
        "has_more_results": true,
        "has_previous_results": false
    },
    "results": [
        {
            "penalty_fixed_id": 1805,
            "clause_fixed_id": 21665,
            "clause_description": "Full-time and part-time production and engineering employees—6 day roster and 7 day roster employees—overtime—Monday to Friday\n",
            "classification_level": 1,
            "penalty_description": "Afternoon and rotating night shift ",
            "rate": 215.0,
            "employee_rate_type_code": "AD",
            "penalty_calculated_value": 63.92,
            "calculated_includes_all_purpose": false,
            "base_pay_rate_id": "BR89757",
            "operative_from": "2025-07-01",
            "operative_to": null,
            "version_number": 8,
            "published_year": 2025,
            "last_modified_datetime": "2025-06-03T01:31:32+00:00"
        }
    ]
}
```

## Database Schema

### Staging Table: `Stg_TblPenalties`

Stores raw penalties data extracted from FWC API.

```sql
CREATE TABLE Stg_TblPenalties (
    id INT IDENTITY(1,1) PRIMARY KEY,
    penalty_fixed_id INT NOT NULL,
    award_code NVARCHAR(50) NOT NULL,
    clause_fixed_id INT NULL,
    clause_description NVARCHAR(2000) NULL,
    classification_level INT NULL,
    penalty_description NVARCHAR(1000) NULL,
    rate DECIMAL(18,2) NULL,
    employee_rate_type_code NVARCHAR(20) NULL,
    penalty_calculated_value DECIMAL(18,4) NULL,
    calculated_includes_all_purpose BIT NULL,
    base_pay_rate_id NVARCHAR(50) NULL,
    operative_from DATETIME2 NULL,
    operative_to DATETIME2 NULL,
    version_number INT NULL,
    last_modified_datetime DATETIME2 NULL,
    published_year INT NULL,
    created_at DATETIME2 DEFAULT GETUTCDATE(),
    updated_at DATETIME2 DEFAULT GETUTCDATE()
);
```

**Indexes:**
- `ix_stg_tblpenalties_award` - Award code lookup
- `ix_stg_tblpenalties_award_year` - Award code + published year
- `ix_stg_tblpenalties_penalty_id` - Penalty fixed ID
- `ix_stg_tblpenalties_classification_level` - Classification level filter
- `ix_stg_tblpenalties_base_pay_rate` - Base pay rate lookup

## ETL Pipeline Integration

### 1. Extract Phase

**Component**: `PenaltiesExtractor` (`src/extract/extractors/penalties.py`)

- Fetches penalties data from FWC API for each award
- Handles pagination automatically (up to 77 pages for MA000120)
- Adds `award_code` to each record
- Logs extraction progress and errors

**Usage**:
```python
from src.extract.extractors.penalties import PenaltiesExtractor
from src.extract.api_client import APIClient

async with APIClient() as client:
    extractor = PenaltiesExtractor(
        api_client=client,
        award_codes=["MA000120", "MA000001"],
        page_size=100
    )
    penalties = await extractor.extract(context)
```

### 2. Transform Phase

Penalties data typically requires minimal transformation as it comes structured from the API.

**Optional Transformations:**
- Parse datetime fields
- Normalize boolean fields
- Validate penalty rates
- Map clause references to existing clauses

### 3. Load Phase

**Component**: `BulkLoader` with `Stg_TblPenalties` table

- Bulk insert/upsert penalties data
- Batch processing (default: 1000 records per batch)
- Duplicate handling based on key columns

**Key Columns** (for upsert):
- `penalty_fixed_id`
- `award_code`
- `published_year`

**Usage**:
```python
from src.load.bulk_loader import BulkLoader

loader = BulkLoader(
    source_key="penalties_extractor",
    table_name="Stg_TblPenalties",
    key_columns=["penalty_fixed_id", "award_code", "published_year"],
    batch_size=1000,
    upsert=True
)
await loader.load(penalties_data, context)
```

## Data Relationships

### Penalties → Pay Rates
- `base_pay_rate_id` → `Stg_TblPayRates.base_pay_rate_id`
- Links penalty calculations to specific base pay rates

### Penalties → Classifications
- `classification_level` → `Stg_TblClassifications.classification_level`
- `award_code` → `Stg_TblClassifications.award_code`
- Links penalties to classification levels

### Penalties → Awards
- `award_code` → `Stg_TblAwards.code`
- Links penalties to specific awards

### Penalties → Clauses
- `clause_fixed_id` → References FWC award clauses
- `clause_description` → Human-readable clause text

## Query Examples

### Get All Penalties for an Award
```sql
SELECT 
    penalty_fixed_id,
    penalty_description,
    rate,
    penalty_calculated_value,
    clause_description,
    classification_level
FROM Stg_TblPenalties
WHERE award_code = 'MA000120'
AND version_number = (SELECT MAX(version_number) FROM Stg_TblPenalties WHERE award_code = 'MA000120')
ORDER BY classification_level, rate;
```

### Get Penalties by Classification Level
```sql
SELECT 
    p.penalty_description,
    p.rate,
    p.penalty_calculated_value,
    c.classification AS classification_name,
    pr.calculated_rate AS base_hourly_rate
FROM Stg_TblPenalties p
LEFT JOIN Stg_TblClassifications c 
    ON p.award_code = c.award_code 
    AND p.classification_level = c.classification_level
LEFT JOIN Stg_TblPayRates pr 
    ON p.base_pay_rate_id = pr.base_pay_rate_id
WHERE p.award_code = 'MA000120'
AND p.classification_level = 1;
```

### Get Penalty Statistics per Award
```sql
SELECT 
    award_code,
    COUNT(*) AS total_penalties,
    AVG(rate) AS avg_penalty_rate,
    MIN(rate) AS min_penalty_rate,
    MAX(rate) AS max_penalty_rate,
    COUNT(DISTINCT classification_level) AS classification_levels
FROM Stg_TblPenalties
GROUP BY award_code
ORDER BY total_penalties DESC;
```

## UI Integration

### API Endpoints (to be created)

**List Penalties**:
```
GET /api/penalties?award_code={code}&classification_level={level}&page=1&limit=100
```

**Response**:
```json
{
    "data": [
        {
            "penalty_fixed_id": 1805,
            "penalty_description": "Afternoon and rotating night shift",
            "rate": 215.0,
            "penalty_calculated_value": 63.92,
            "classification_level": 1,
            "clause_description": "...",
            "base_pay_rate_id": "BR89757"
        }
    ],
    "pagination": {
        "page": 1,
        "limit": 100,
        "total": 7700,
        "pages": 77
    }
}
```

### UI Components (React/Next.js)

**Penalties Table Component**:
```jsx
import React, { useState, useEffect } from 'react';

const PenaltiesTable = ({ awardCode }) => {
    const [penalties, setPenalties] = useState([]);
    const [loading, setLoading] = useState(true);
    const [page, setPage] = useState(1);
    const [filters, setFilters] = useState({
        classification_level: null,
        employee_rate_type_code: null
    });

    useEffect(() => {
        fetchPenalties();
    }, [awardCode, page, filters]);

    const fetchPenalties = async () => {
        setLoading(true);
        const params = new URLSearchParams({
            award_code: awardCode,
            page,
            limit: 100,
            ...filters
        });
        
        const response = await fetch(`/api/penalties?${params}`);
        const data = await response.json();
        setPenalties(data.data);
        setLoading(false);
    };

    return (
        <div className="penalties-table">
            <div className="filters">
                <select 
                    onChange={(e) => setFilters({...filters, classification_level: e.target.value})}
                    value={filters.classification_level || ''}
                >
                    <option value="">All Levels</option>
                    <option value="1">Level 1</option>
                    <option value="2">Level 2</option>
                    {/* Add more levels */}
                </select>
            </div>

            {loading ? (
                <div>Loading...</div>
            ) : (
                <table>
                    <thead>
                        <tr>
                            <th>Description</th>
                            <th>Rate %</th>
                            <th>Calculated Value</th>
                            <th>Level</th>
                            <th>Clause</th>
                        </tr>
                    </thead>
                    <tbody>
                        {penalties.map(penalty => (
                            <tr key={penalty.penalty_fixed_id}>
                                <td>{penalty.penalty_description}</td>
                                <td>{penalty.rate}%</td>
                                <td>${penalty.penalty_calculated_value}</td>
                                <td>{penalty.classification_level}</td>
                                <td>{penalty.clause_description}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            )}

            <div className="pagination">
                <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}>
                    Previous
                </button>
                <span>Page {page}</span>
                <button onClick={() => setPage(p => p + 1)}>
                    Next
                </button>
            </div>
        </div>
    );
};

export default PenaltiesTable;
```

## Integration with Rule Engine

### Linking Penalties to JSON Rules

Penalties data from FWC can be used to populate the JSON-based rule engine:

```sql
-- Generate penalty rules from penalties data
INSERT INTO TblPenaltyRulesJSON (
    rule_id,
    award_code,
    name,
    priority,
    status,
    rule_json,
    fwc_clause_reference,
    created_at
)
SELECT 
    'PEN_' + CAST(penalty_fixed_id AS NVARCHAR),
    award_code,
    penalty_description,
    100 + penalty_fixed_id % 1000 AS priority,
    'Active' AS status,
    JSON_QUERY('{
        "if": {
            "classification_level": ' + CAST(classification_level AS NVARCHAR) + ',
            "employee_rate_type_code": "' + employee_rate_type_code + '"
        },
        "then": {
            "apply_multiplier": ' + CAST(rate / 100.0 AS NVARCHAR) + ',
            "apply_to": ["hourly_rate"],
            "note": "' + penalty_description + '"
        }
    }'),
    clause_fixed_id,
    GETUTCDATE()
FROM Stg_TblPenalties
WHERE award_code = 'MA000120'
AND published_year = 2025;
```

## Sprint 31 Integration

### Sprint 31-A: Awards Management

**Penalties in Award Management**:
- Display penalties when viewing award details
- Show penalty rates alongside base pay rates
- Allow filtering penalties by classification level
- Sync penalties data when syncing awards from FWC

### Sprint 31-B: Custom Rules for Awards

**Create Custom Penalty Rules**:
- Use FWC penalties data as baseline
- Allow customization of penalty rates for tenant-specific needs
- Maintain FWC compliance while supporting business rules
- Validate custom rates meet minimum FWC requirements

### System Admin Capabilities

**Penalties Management**:
1. **View All Penalties**: Browse complete penalties data for all awards
2. **Filter & Search**: Filter by award, classification level, penalty type
3. **Compare**: Compare penalty rates across different awards
4. **Export**: Export penalties data for analysis
5. **Sync**: Refresh penalties data from FWC API
6. **Assign**: Assign specific penalty rules to tenants

## Performance Considerations

### Data Volume
- MA000120 has ~7,700 penalty records
- Some awards may have 10,000+ penalty records
- Total across all awards: 100,000+ records

### Optimization Strategies
1. **Pagination**: Always paginate results (100-500 records per page)
2. **Indexes**: Use indexes on award_code, classification_level, penalty_fixed_id
3. **Caching**: Cache frequently accessed penalties data
4. **Filtering**: Apply filters server-side before returning data
5. **Batch Loading**: Use bulk operations for ETL (1000 records per batch)

## Error Handling

### Common Errors

**API Rate Limiting**:
- FWC API may throttle requests
- Implement exponential backoff
- Use connection pooling

**Missing Data**:
- Some awards may have no penalties
- Handle null/empty responses gracefully
- Log warnings for awards without penalties

**Data Validation**:
- Validate penalty rates (should be positive)
- Check clause references exist
- Verify classification level mappings

## Testing

### Unit Tests
```python
async def test_penalties_extractor():
    """Test penalties extraction from FWC API"""
    async with APIClient() as client:
        extractor = PenaltiesExtractor(client, ["MA000120"])
        context = PipelineContext()
        
        penalties = await extractor.extract(context)
        
        assert len(penalties) > 0
        assert penalties[0]["award_code"] == "MA000120"
        assert "penalty_fixed_id" in penalties[0]
        assert "rate" in penalties[0]
```

### Integration Tests
```sql
-- Verify penalties loaded correctly
SELECT COUNT(*) FROM Stg_TblPenalties WHERE award_code = 'MA000120';
-- Expected: ~7700 records

-- Verify relationships
SELECT COUNT(*) 
FROM Stg_TblPenalties p
INNER JOIN Stg_TblPayRates pr ON p.base_pay_rate_id = pr.base_pay_rate_id
WHERE p.award_code = 'MA000120';
-- Should return records with valid pay rate links
```

## Deployment Steps

1. **Run Database Migration**:
   ```bash
   sqlcmd -S <server> -d <database> -i migrations/sql/010_create_penalties_staging_table.sql
   ```

2. **Deploy Code Changes**:
   - Deploy `PenaltiesExtractor`
   - Deploy `Penalty` model
   - Deploy UI components

3. **Run Initial Load**:
   ```bash
   python run.py --extract penalties --awards MA000120
   ```

4. **Verify Data**:
   ```sql
   SELECT award_code, COUNT(*) 
   FROM Stg_TblPenalties 
   GROUP BY award_code;
   ```

5. **Enable UI Access**:
   - Deploy UI changes
   - Configure API endpoints
   - Test filtering and pagination

## Maintenance

### Scheduled Sync
- Run penalties ETL daily or weekly
- Sync with FWC API to get latest penalty data
- Update version numbers when FWC publishes new data

### Monitoring
- Track extraction success/failure rates
- Monitor API response times
- Alert on data anomalies (e.g., sudden drop in penalty count)

### Data Cleanup
- Archive old versions of penalties data
- Maintain only current + previous 2 versions
- Implement soft deletes for audit trail

## Summary

The penalties integration provides:
- ✅ Complete FWC penalties data extraction
- ✅ Efficient storage in staging table with indexes
- ✅ Relationships to pay rates and classifications
- ✅ UI components for filtering and display
- ✅ Integration with JSON rule engine
- ✅ Support for Sprint 31 requirements
- ✅ Scalable architecture for 100,000+ records
