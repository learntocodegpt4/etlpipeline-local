# FWC ETL Pipeline API Documentation

This document describes the REST API endpoints for the FWC Modern Awards ETL Pipeline.

## Base URL

- **Development**: `http://localhost:8000/api` or `http://localhost:8081/api` (via Nginx)
- **Production**: Configure based on your deployment

## Authentication

Currently, the API does not require authentication. For production deployments, implement appropriate authentication (API keys, OAuth, etc.).

## Endpoints

### Status

#### Health Check

```http
GET /api/status
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "database_connected": true,
  "scheduler_running": true,
  "version": "1.0.0"
}
```

#### Detailed Status

```http
GET /api/status/detailed
```

**Response:**
```json
{
  "api": {
    "status": "running",
    "version": "1.0.0",
    "timestamp": "2024-01-15T10:30:00Z"
  },
  "database": {
    "status": "connected",
    "host": "localhost",
    "database": "etl_pipeline"
  },
  "scheduler": {
    "status": "running",
    "enabled": true,
    "cron_expression": "0 2 * * *",
    "scheduled_jobs": [
      {
        "id": "etl_scheduled_job",
        "name": "ETL Pipeline Scheduled Job",
        "next_run": "2024-01-16T02:00:00Z"
      }
    ]
  },
  "last_job": {
    "job_id": "abc123...",
    "status": "completed",
    "start_time": "2024-01-15T02:00:00Z"
  },
  "config": {
    "fwc_api_url": "https://api.fwc.gov.au/api/v1",
    "page_size": 100,
    "log_level": "INFO"
  }
}
```

---

### Jobs

#### List Jobs

```http
GET /api/jobs?page=1&page_size=20&status=completed
```

**Query Parameters:**
| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| page | int | Page number (1-based) | 1 |
| page_size | int | Results per page (1-100) | 20 |
| status | string | Filter by status (pending, running, completed, failed) | - |

**Response:**
```json
{
  "jobs": [
    {
      "job_id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "completed",
      "start_time": "2024-01-15T02:00:00Z",
      "end_time": "2024-01-15T02:15:30Z",
      "duration_seconds": 930.5,
      "total_records_processed": 15234,
      "error_count": 0,
      "warning_count": 2,
      "error_message": null
    }
  ],
  "total": 150,
  "page": 1,
  "page_size": 20
}
```

#### Get Job Details

```http
GET /api/jobs/{job_id}
```

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "start_time": "2024-01-15T02:00:00Z",
  "end_time": "2024-01-15T02:15:30Z",
  "duration_seconds": 930.5,
  "total_records_processed": 15234,
  "error_count": 0,
  "warning_count": 2,
  "error_message": null,
  "steps": [
    {
      "step_name": "awards_extractor",
      "status": "completed",
      "start_time": "2024-01-15T02:00:00Z",
      "end_time": "2024-01-15T02:00:30Z",
      "duration_seconds": 30.2,
      "records_processed": 156,
      "records_failed": 0,
      "error_message": null
    },
    {
      "step_name": "classifications_extractor",
      "status": "completed",
      "start_time": "2024-01-15T02:00:30Z",
      "end_time": "2024-01-15T02:05:00Z",
      "duration_seconds": 270.0,
      "records_processed": 5234,
      "records_failed": 0,
      "error_message": null
    }
  ]
}
```

#### Get Job Logs

```http
GET /api/jobs/{job_id}/logs
```

**Response:**
```json
[
  {
    "step_name": "awards_extractor",
    "status": "completed",
    "start_time": "2024-01-15T02:00:00Z",
    "end_time": "2024-01-15T02:00:30Z",
    "duration_seconds": 30.2,
    "records_processed": 156,
    "records_failed": 0,
    "error_message": null
  }
]
```

#### Trigger Job

```http
POST /api/jobs/trigger
Content-Type: application/json

{
  "award_codes": ["MA000001", "MA000002"]
}
```

**Request Body:**
| Field | Type | Description | Required |
|-------|------|-------------|----------|
| award_codes | string[] | Specific award codes to process (null for all) | No |

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440001",
  "message": "ETL pipeline triggered successfully"
}
```

#### Get Job Statistics

```http
GET /api/jobs/stats/summary?days=7
```

**Query Parameters:**
| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| days | int | Number of days to include (1-30) | 7 |

**Response:**
```json
{
  "total": 42,
  "by_status": {
    "completed": 35,
    "failed": 3,
    "pending": 2,
    "running": 2
  },
  "avg_duration": 890.5,
  "total_records": 523400
}
```

---

### Data Preview

#### List Tables

```http
GET /api/data/tables
```

**Response:**
```json
{
  "tables": [
    {"table": "awards", "record_count": 156},
    {"table": "classifications", "record_count": 15234},
    {"table": "pay_rates", "record_count": 52340},
    {"table": "expense_allowances", "record_count": 8234},
    {"table": "wage_allowances", "record_count": 4521}
  ]
}
```

#### Preview Table Data

```http
GET /api/data/preview/{table}?page=1&page_size=50&award_code=MA000001
```

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| table | string | Table name (awards, classifications, pay_rates, expense_allowances, wage_allowances) |

**Query Parameters:**
| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| page | int | Page number (1-based) | 1 |
| page_size | int | Results per page (1-500) | 50 |
| award_code | string | Filter by award code | - |

**Response:**
```json
{
  "table": "awards",
  "total_count": 156,
  "page": 1,
  "page_size": 50,
  "data": [
    {
      "id": 1,
      "award_id": 1752,
      "award_fixed_id": 1,
      "code": "MA000001",
      "name": "Black Coal Mining Industry Award 2020",
      "award_operative_from": "2010-01-01T00:00:00",
      "award_operative_to": null,
      "version_number": 3,
      "published_year": 2025,
      "created_at": "2024-01-15T02:00:00Z",
      "updated_at": "2024-01-15T02:00:00Z"
    }
  ]
}
```

#### List Awards

```http
GET /api/data/awards?page=1&page_size=100
```

**Response:**
```json
{
  "awards": [
    {"code": "MA000001", "name": "Black Coal Mining Industry Award 2020"},
    {"code": "MA000002", "name": "Clerks—Private Sector Award 2020"}
  ],
  "total": 156,
  "page": 1,
  "page_size": 100
}
```

---

### WebSocket

#### Real-time Log Streaming

```javascript
const ws = new WebSocket('ws://localhost:8081/ws/logs');

ws.onopen = () => {
  console.log('Connected to log stream');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Log:', data);
};

// Send ping to keep connection alive
ws.send('ping');
```

**Message Types:**

1. **Connected:**
```json
{
  "type": "connected",
  "timestamp": "2024-01-15T10:30:00Z",
  "message": "Connected to log stream"
}
```

2. **Heartbeat:**
```json
{
  "type": "heartbeat",
  "timestamp": "2024-01-15T10:30:30Z"
}
```

3. **Log:**
```json
{
  "type": "log",
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "message": "Extracting awards data",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "step": "awards_extractor",
  "details": {}
}
```

4. **Job Event:**
```json
{
  "type": "job_event",
  "timestamp": "2024-01-15T10:30:00Z",
  "event": "job_started",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "details": {}
}
```

---

## Error Responses

All endpoints return errors in a consistent format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

**HTTP Status Codes:**
| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request - Invalid parameters |
| 404 | Not Found - Resource does not exist |
| 500 | Internal Server Error |

---

## Rate Limiting

The API does not currently implement rate limiting. For production, consider:
- Implementing rate limiting at the Nginx level
- Adding API key-based rate limits
- Using Azure API Management for comprehensive rate limiting

---

## Examples

### cURL Examples

**Get system status:**
```bash
curl -X GET "http://localhost:8081/api/status"
```

**Trigger ETL job:**
```bash
curl -X POST "http://localhost:8081/api/jobs/trigger" \
  -H "Content-Type: application/json" \
  -d '{"award_codes": null}'
```

**Get job details:**
```bash
curl -X GET "http://localhost:8081/api/jobs/550e8400-e29b-41d4-a716-446655440000"
```

**Preview data:**
```bash
curl -X GET "http://localhost:8081/api/data/preview/awards?page=1&page_size=10"
```

### Python Examples

```python
import httpx

API_URL = "http://localhost:8081/api"

# Get status
response = httpx.get(f"{API_URL}/status")
print(response.json())

# Trigger job
response = httpx.post(
    f"{API_URL}/jobs/trigger",
    json={"award_codes": ["MA000001"]}
)
print(response.json())

# Get jobs
response = httpx.get(f"{API_URL}/jobs", params={"page": 1, "page_size": 10})
print(response.json())
```

### JavaScript Examples

```javascript
// Get status
const status = await fetch('http://localhost:8081/api/status')
  .then(res => res.json());

// Trigger job
const result = await fetch('http://localhost:8081/api/jobs/trigger', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ award_codes: null })
}).then(res => res.json());

// WebSocket for logs
const ws = new WebSocket('ws://localhost:8081/ws/logs');
ws.onmessage = (event) => console.log(JSON.parse(event.data));
```
