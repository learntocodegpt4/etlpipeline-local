# FWC Modern Awards ETL Pipeline

A complete Python ETL pipeline that extracts data from the FWC (Fair Work Commission) Modern Awards REST API, transforms JSON responses, and loads them into MS SQL Server tables.

## Features

- **Modular Architecture**: Reusable ETL core library that runs standalone, in Docker, or on Azure
- **Extract Module**: HTTP client with retry logic using `httpx` + `tenacity`
- **Transform Module**: Data validation, type conversion, and JSON flattening
- **Load Module**: MS SQL Server bulk insert with upsert logic
- **FastAPI Backend**: REST API for job management and data preview
- **Next.js Dashboard**: Real-time monitoring UI with MUI components
- **Docker Support**: Container deployment with Docker Compose
- **Nginx Reverse Proxy**: Configuration for external access on port 8081

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- MS SQL Server (existing container or instance)
- Nginx (for reverse proxy)
- Docker & Docker Compose (optional)

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd etlpipeline-local
   ```

2. **Create Python virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate     # Windows
   ```

3. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run database migrations:**
   ```bash
   # Using sqlcmd or your preferred SQL client
   sqlcmd -S localhost -d etl_pipeline -i migrations/sql/001_create_base_tables.sql
   sqlcmd -S localhost -d etl_pipeline -i migrations/sql/002_create_etl_tracking_tables.sql
   ```

6. **Install UI dependencies:**
   ```bash
   cd ui
   npm install
   ```

### Running the Application

#### Option 1: Run Individually

**Start FastAPI backend:**
```bash
python run.py --mode api
# or
uvicorn src.api.app:app --host 0.0.0.0 --port 8000
```

**Start Next.js UI:**
```bash
cd ui
npm run dev
```

**Run ETL Pipeline once:**
```bash
python run.py --mode run
```

**Run with scheduler:**
```bash
python run.py --mode schedule
```

#### Option 2: Docker Compose

```bash
cd docker
docker-compose up -d
```

### Nginx Setup

1. Copy the example configuration:
   ```bash
   cp nginx/nginx.conf.example C:/nginx/conf/nginx.conf  # Windows
   # or
   sudo cp nginx/nginx.conf.example /etc/nginx/nginx.conf  # Linux
   ```

2. Test and reload Nginx:
   ```bash
   nginx -t
   nginx -s reload
   ```

3. Access the application at `http://localhost:8081`

## Project Structure

```
etlpipeline-local/
├── docker/                 # Docker configuration
│   ├── Dockerfile          # Python ETL + FastAPI
│   ├── Dockerfile.ui       # Next.js UI
│   └── docker-compose.yml  # Service orchestration
├── src/                    # Python source code
│   ├── config/             # Configuration settings
│   ├── core/               # Pipeline interfaces
│   ├── extract/            # Data extraction
│   ├── transform/          # Data transformation
│   ├── load/               # Database loading
│   ├── orchestrator/       # Pipeline coordination
│   ├── api/                # FastAPI backend
│   └── utils/              # Utilities
├── ui/                     # Next.js frontend
│   ├── src/app/            # App router pages
│   ├── src/components/     # React components
│   └── src/lib/            # API client & utilities
├── migrations/sql/         # SQL migration scripts
├── docs/                   # Documentation
│   ├── config_setup.md     # Nginx configuration
│   ├── azure_migration.md  # Azure deployment guide
│   └── api_documentation.md
├── nginx/                  # Nginx configuration
├── tests/                  # Test files
├── .env.example            # Environment template
├── requirements.txt        # Python dependencies
└── pyproject.toml          # Python project config
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FWC_API_BASE_URL` | FWC API base URL | https://api.fwc.gov.au/api/v1 |
| `FWC_API_KEY` | API key (Ocp-Apim-Subscription-Key) | - |
| `MSSQL_HOST` | MS SQL Server host | localhost |
| `MSSQL_PORT` | MS SQL Server port | 1433 |
| `MSSQL_DATABASE` | Database name | etl_pipeline |
| `MSSQL_USER` | Database user | sa |
| `MSSQL_PASSWORD` | Database password | - |
| `API_HOST` | FastAPI host | 0.0.0.0 |
| `API_PORT` | FastAPI port | 8000 |
| `ETL_SCHEDULE_ENABLED` | Enable scheduler | true |
| `ETL_CRON_EXPRESSION` | Cron schedule | 0 2 * * * |
| `LOG_LEVEL` | Logging level | INFO |

### FWC API Endpoints

The pipeline extracts data from:
- `/api/v1/awards` - Award master data
- `/api/v1/awards/{code}/classifications` - Classifications
- `/api/v1/awards/{code}/pay-rates` - Pay rates
- `/api/v1/awards/{code}/expense-allowances` - Expense allowances
- `/api/v1/awards/{code}/wage-allowances` - Wage allowances

## API Endpoints

### Jobs
- `GET /api/jobs` - List all ETL jobs
- `GET /api/jobs/{job_id}` - Get job details
- `POST /api/jobs/trigger` - Manually trigger pipeline
- `GET /api/jobs/{job_id}/logs` - Get job logs
- `GET /api/jobs/stats/summary` - Get statistics

### Status
- `GET /api/status` - Health check
- `GET /api/status/detailed` - Detailed status

### Data
- `GET /api/data/tables` - List tables
- `GET /api/data/preview/{table}` - Preview table data
- `GET /api/data/awards` - List awards

### WebSocket
- `WS /ws/logs` - Real-time log streaming

See [API Documentation](docs/api_documentation.md) for full details.

## Docker Deployment

```bash
# Build and start all services
cd docker
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

**Note:** The docker-compose configuration does NOT include MS SQL Server. It uses an existing MS SQL container on the host via `host.docker.internal`.

## Database Schema

Tables created by migrations:
- `awards` - Award master data
- `classifications` - Award classifications
- `pay_rates` - Pay rate information
- `expense_allowances` - Expense allowance data
- `wage_allowances` - Wage allowance data
- `etl_job_logs` - Job execution history
- `etl_job_details` - Step-by-step logs
- `raw_api_responses` - Raw JSON storage

## UI Features

The Next.js dashboard provides:
- **Dashboard**: Job statistics and charts
- **Jobs**: Job history with filtering and pagination
- **Job Detail**: Step-by-step progress view
- **Data**: Preview data from all tables
- **Live Logs**: Real-time log streaming via WebSocket

## Azure Migration

The ETL pipeline is designed to be portable. See [Azure Migration Guide](docs/azure_migration.md) for deployment options:
- Azure Functions (serverless)
- Azure Container Instances
- Azure App Service
- Azure Virtual Machines

## Troubleshooting

### Common Issues

1. **Database connection fails:**
   - Verify MS SQL Server is running
   - Check connection string in `.env`
   - Ensure ODBC driver is installed

2. **API returns 502:**
   - Check if FastAPI is running on port 8000
   - Verify Nginx configuration

3. **UI won't load:**
   - Check if Next.js is running on port 3000
   - Verify environment variables

4. **WebSocket disconnects:**
   - Increase `proxy_read_timeout` in Nginx

### Logs

```bash
# Python logs
tail -f logs/etl.log

# Docker logs
docker-compose logs -f etl-api

# Nginx logs
tail -f /var/log/nginx/error.log  # Linux
type C:\nginx\logs\error.log      # Windows
```

## Development

### Running Tests

```bash
pytest tests/
```

### Code Quality

```bash
# Linting
ruff check src/

# Formatting
black src/

# Type checking
mypy src/
```

## License

MIT License - see LICENSE file for details.

## Support

For issues and feature requests, please use the GitHub issue tracker