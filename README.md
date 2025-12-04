# FWC ETL Pipeline

A complete Python ETL pipeline for extracting data from the FWC (Fair Work Commission) Modern Awards REST API, transforming JSON responses, and loading them into MS SQL Server. The solution is portable across Windows 11 Pro, Docker/Kubernetes, Azure Functions, and Azure VMs.

## Features

- **Modular Architecture**: Reusable ETL core that runs standalone, in Docker, as Azure Functions, or on Azure VMs
- **Complete ETL Pipeline**: Extract, Transform, Load with comprehensive error handling
- **API Endpoints**: Awards, Classifications, Pay Rates, Expense Allowances, Wage Allowances
- **FastAPI Backend**: REST API for job management and monitoring
- **React/Next.js UI**: Real-time dashboard with Material UI
- **Scheduling**: APScheduler for cron-based automation
- **State Management**: SQLite for local job tracking
- **Observability**: Structured logging with log rotation

## Prerequisites

- Python 3.11+
- Node.js 20+ (for UI)
- MS SQL Server 2019+ (or SQL Server in Docker)
- ODBC Driver 18 for SQL Server

## Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/your-org/etlpipeline-local.git
cd etlpipeline-local

# Create Python virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your settings
# Required: FWC_API_KEY, MSSQL_* settings
```

### 3. Run Database Migrations

```bash
python run.py --migrate
```

### 4. Run ETL Pipeline

```bash
# Run full ETL once
python run.py --mode run

# Run specific pipeline
python run.py --mode run --pipeline awards

# Run with scheduler
python run.py --mode schedule

# Run API server
python run.py --mode api
```

## Docker Deployment

### Using Docker Compose

```bash
cd docker

# Set your API key
export FWC_API_KEY=your_api_key_here

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

Services:
- **etl-api**: FastAPI backend at http://localhost:8000
- **etl-ui**: Next.js dashboard at http://localhost:3000
- **etl-worker**: Scheduled ETL worker
- **mssql**: MS SQL Server at localhost:1433

### Build Images Separately

```bash
# Build ETL/API image
docker build -f docker/Dockerfile -t fwc-etl-pipeline .

# Build UI image
docker build -f docker/Dockerfile.ui -t fwc-etl-ui .
```

## Project Structure

```
etlpipeline-local/
├── docker/                    # Docker configuration
│   ├── Dockerfile             # Python ETL + FastAPI
│   ├── Dockerfile.ui          # Next.js UI
│   └── docker-compose.yml     # All services
├── src/
│   ├── config/                # Configuration management
│   │   ├── settings.py        # Pydantic settings
│   │   └── api_endpoints.py   # API endpoint definitions
│   ├── core/                  # Reusable ETL core (Azure-ready)
│   │   ├── interfaces.py      # Abstract base classes
│   │   └── pipeline.py        # Pipeline orchestration
│   ├── extract/               # Data extraction
│   │   ├── api_client.py      # HTTP client with retry
│   │   ├── paginator.py       # Pagination handler
│   │   └── extractors/        # Endpoint-specific extractors
│   ├── transform/             # Data transformation
│   │   ├── base_transformer.py
│   │   ├── validators.py      # Data validation
│   │   └── transformers/      # Entity transformers
│   ├── load/                  # Data loading
│   │   ├── sql_connector.py   # SQLAlchemy connection
│   │   ├── bulk_loader.py     # Bulk insert/upsert
│   │   └── models/            # SQLAlchemy models
│   ├── orchestrator/          # Pipeline coordination
│   │   ├── pipeline.py        # ETL orchestrator
│   │   ├── scheduler.py       # APScheduler wrapper
│   │   └── state_manager.py   # SQLite state management
│   ├── api/                   # FastAPI backend
│   │   ├── app.py             # Main FastAPI app
│   │   └── routes/            # API routes
│   └── utils/                 # Utilities
│       ├── logging.py         # Structured logging
│       └── helpers.py         # Helper functions
├── ui/                        # Next.js React UI
│   ├── src/app/               # App Router pages
│   ├── src/components/        # React components
│   └── src/lib/               # API client library
├── migrations/sql/            # SQL Server migrations
├── azure/                     # Azure Functions templates
├── tests/                     # Test suite
├── .env.example               # Environment template
├── requirements.txt           # Python dependencies
├── pyproject.toml             # Project configuration
└── run.py                     # Main entry point
```

## API Endpoints

### Jobs API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/jobs` | GET | List all ETL jobs |
| `/api/jobs/{job_id}` | GET | Get job details |
| `/api/jobs/{job_id}/logs` | GET | Get job logs |
| `/api/jobs/trigger` | POST | Trigger ETL pipeline |
| `/api/jobs/stats/summary` | GET | Get job statistics |

### Status API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/status` | GET | System health check |
| `/api/status/config` | GET | View configuration |

### Data API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/data/tables` | GET | List available tables |
| `/api/data/preview/{table}` | GET | Preview table data |
| `/api/data/stats/{table}` | GET | Get table statistics |

### WebSocket

| Endpoint | Description |
|----------|-------------|
| `/ws/logs` | Real-time log streaming |
| `/ws/jobs/{job_id}` | Job-specific log streaming |

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FWC_API_BASE_URL` | FWC API base URL | https://api.fwc.gov.au/api/v1 |
| `FWC_API_KEY` | API subscription key | (required) |
| `FWC_API_TIMEOUT` | Request timeout (seconds) | 30 |
| `FWC_API_PAGE_SIZE` | Records per page | 100 |
| `MSSQL_HOST` | SQL Server hostname | localhost |
| `MSSQL_PORT` | SQL Server port | 1433 |
| `MSSQL_DATABASE` | Database name | fwc_awards |
| `MSSQL_USERNAME` | Database username | sa |
| `MSSQL_PASSWORD` | Database password | (required) |
| `SCHEDULER_ENABLED` | Enable scheduler | true |
| `SCHEDULER_CRON_EXPRESSION` | Schedule cron | 0 2 * * * |
| `LOG_LEVEL` | Logging level | INFO |

## Azure Migration

### Azure Functions Deployment

1. Create Azure Functions app with Python 3.11 runtime
2. Configure application settings with environment variables
3. Deploy the `azure/function_app.py` along with `src/` package

```bash
# Using Azure Functions Core Tools
func azure functionapp publish <function-app-name>
```

### Azure VM Deployment

1. Create Azure VM with Python 3.11
2. Install ODBC Driver 18 for SQL Server
3. Clone repository and install dependencies
4. Configure environment and run with scheduler

```bash
# Install as systemd service
sudo cp etl-pipeline.service /etc/systemd/system/
sudo systemctl enable etl-pipeline
sudo systemctl start etl-pipeline
```

## Database Schema

The pipeline creates and manages the following tables:

- `awards` - Award master data
- `classifications` - Award classifications
- `pay_rates` - Pay rate information
- `expense_allowances` - Expense allowance data
- `wage_allowances` - Wage allowance data
- `etl_job_logs` - Job execution history
- `etl_job_details` - Step-by-step logs
- `raw_api_responses` - Raw JSON from API

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html
```

### Code Quality

```bash
# Lint with ruff
ruff check src/

# Type checking
mypy src/
```

### UI Development

```bash
cd ui
npm install
npm run dev
```

## Troubleshooting

### Connection Issues

1. Verify SQL Server is running and accessible
2. Check ODBC driver is installed correctly
3. Verify firewall allows port 1433

### API Key Issues

1. Ensure `Ocp-Apim-Subscription-Key` header is set
2. Check API key is valid and not expired
3. Verify rate limits are not exceeded

### Docker Issues

```bash
# Check container logs
docker-compose logs etl-api

# Rebuild images
docker-compose build --no-cache

# Reset volumes
docker-compose down -v
```

## License

MIT License

## Support

For issues and questions, please open a GitHub issue