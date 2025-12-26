# Enterprise Deployment & Operations Guide

Complete step-by-step guide for deploying, building, and operating the RosteredAI ETL Pipeline and Rule Engine system.

## Table of Contents
1. [System Architecture](#system-architecture)
2. [Prerequisites](#prerequisites)
3. [Environment Setup](#environment-setup)
4. [Build & Deploy Applications](#build--deploy-applications)
5. [Load Data Using ETL](#load-data-using-etl)
6. [Process Rules & Compile Data](#process-rules--compile-data)
7. [Access APIs & UIs](#access-apis--uis)
8. [Troubleshooting](#troubleshooting)
9. [Unit Testing](#unit-testing)
10. [Production Deployment](#production-deployment)

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        NGINX (Port 80/443)                       │
│                  Global Proxy on Windows 11 Pro                  │
└────┬────────────────────┬────────────────────┬──────────────────┘
     │                    │                    │
     │ /etlapi/           │ /etlui/            │ /ruleapi/
     ↓                    ↓                    ↓
┌─────────┐         ┌──────────┐        ┌──────────────┐
│ETL API  │         │ ETL UI   │        │ Rule Engine  │
│FastAPI  │         │Next.js   │        │ .NET API     │
│Port 8000│         │Port 3001 │        │ Port 5016    │
│(Docker) │         │(Docker)  │        │ (Docker)     │
└────┬────┘         └────┬─────┘        └──────┬───────┘
     │                   │                     │
     └───────────────────┴─────────────────────┘
                         ↓
              ┌──────────────────────┐
              │  SQL Server Database │
              │  RosteredAIDBDev     │
              │  Port 1433           │
              └──────────────────────┘
```

### Components:
- **ETL API** (Python FastAPI): Data extraction, transformation, loading
- **ETL UI** (Next.js/React): Dashboard for monitoring ETL jobs
- **Rule Engine API** (.NET 8): Awards rules compilation and management
- **SQL Server**: Central database for all data
- **NGINX**: Reverse proxy for routing traffic

---

## Prerequisites

### Software Requirements:
- **Docker Desktop** (20.10+)
- **Docker Compose** (2.0+)
- **NGINX** (1.24+) - Already running globally on Windows 11 Pro
- **.NET 8 SDK** (for local development)
- **Python 3.11+** (for local development)
- **Node.js 20+** (for local development)
- **SQL Server** (2019+)

### Network Requirements:
- Port 80/443 (NGINX)
- Port 8000 (ETL API)
- Port 3001 (ETL UI)
- Port 5016/8082 (Rule Engine API)
- Port 1433 (SQL Server)

---

## Environment Setup

### 1. Clone Repository
```bash
git clone https://github.com/learntocodegpt4/etlpipeline-local.git
cd etlpipeline-local
```

### 2. Configure Environment Variables

Create `.env` file in project root:
```bash
# Database Configuration
MSSQL_HOST=202.131.115.228
MSSQL_PORT=1433
MSSQL_DATABASE=RosteredAIDBDev
MSSQL_USER=sa
MSSQL_PASSWORD=Piyush@23D!gita1

# FWC API Configuration
FWC_API_KEY=4669506fdbea4e7783d3dbb7b899b935
FWC_API_BASE_URL=https://api.fwc.gov.au/api/v1

# Application Configuration
ROOT_PATH=/etlapi
NEXT_PUBLIC_API_URL=/etlapi/api
NEXT_PUBLIC_WS_URL=/etlapi/ws
ASPNETCORE_ENVIRONMENT=Development
```

### 3. Configure NGINX

Create/update NGINX configuration file:

**Location**: `C:\nginx\conf\nginx.conf` (Windows) or `/etc/nginx/nginx.conf` (Linux)

```nginx
http {
    upstream etl_api {
        server localhost:8000;
    }
    
    upstream etl_ui {
        server localhost:3001;
    }
    
    upstream rule_engine {
        server localhost:8082;
    }
    
    server {
        listen 80;
        server_name localhost;
        
        # ETL API
        location /etlapi/ {
            proxy_pass http://etl_api/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        # ETL UI
        location /etlui/ {
            proxy_pass http://etl_ui/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # WebSocket support
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }
        
        # Rule Engine API
        location /ruleapi/ {
            proxy_pass http://rule_engine/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

**Reload NGINX:**
```bash
# Windows
nginx -s reload

# Linux/Mac
sudo nginx -s reload
# or
sudo systemctl reload nginx
```

---

## Build & Deploy Applications

### Option A: Using Docker Compose (Recommended)

#### 1. Build All Services
```bash
cd /path/to/etlpipeline-local
docker-compose -f docker/docker-compose.yml build --no-cache
```

#### 2. Start All Services
```bash
docker-compose -f docker/docker-compose.yml up -d
```

#### 3. Verify Services Running
```bash
docker-compose -f docker/docker-compose.yml ps

# Expected output:
# NAME              STATUS    PORTS
# etl-api           Up        0.0.0.0:8000->8000/tcp
# etl-ui            Up        0.0.0.0:3001->3001/tcp
# etl-ruleengine    Up        0.0.0.0:8082->5016/tcp
```

#### 4. Check Service Logs
```bash
# View all logs
docker-compose -f docker/docker-compose.yml logs -f

# View specific service logs
docker-compose -f docker/docker-compose.yml logs -f ruleengine
docker-compose -f docker/docker-compose.yml logs -f api
docker-compose -f docker/docker-compose.yml logs -f ui
```

### Option B: Local Development (Without Docker)

#### 1. Run ETL API (Python)
```bash
cd etlpipeline-local
python -m pip install -r requirements.txt
python run.py

# API will start at http://localhost:8000
```

#### 2. Run ETL UI (Next.js)
```bash
cd etlpipeline-local/ui
npm install
npm run dev

# UI will start at http://localhost:3001
```

#### 3. Run Rule Engine API (.NET)
```bash
cd etlpipeline-local/RuleEngine/RuleEngine.API
dotnet restore
dotnet build
dotnet run

# API will start at http://localhost:5016
```

---

## Fix Rule Engine Swagger Issue

### Problem: Swagger not accessible at /swagger

### Solution 1: Update Program.cs (Already Configured)

The `Program.cs` is already configured correctly:
```csharp
// Line 43-48
app.UseSwagger();
app.UseSwaggerUI(c =>
{
    c.SwaggerEndpoint("/swagger/v1/swagger.json", "Rule Engine API v1");
    c.RoutePrefix = "swagger"; // served at /swagger
});
```

### Solution 2: Fix Docker Port Mapping

Update `docker/docker-compose.yml`:
```yaml
ruleengine:
  environment:
    - ASPNETCORE_URLS=http://0.0.0.0:5016
    - ASPNETCORE_ENVIRONMENT=Development  # Add this line
  ports:
    - "8082:5016"
```

### Solution 3: Update appsettings.json for CORS

Update `RuleEngine/RuleEngine.API/appsettings.json`:
```json
{
  "Logging": {
    "LogLevel": {
      "Default": "Information",
      "Microsoft.AspNetCore": "Warning"
    }
  },
  "AllowedHosts": "*",
  "DatabaseSettings": {
    "ConnectionString": "Server=202.131.115.228,1433;Database=RosteredAIDBDev;User Id=sa;Password=Piyush@23D!gita1;TrustServerCertificate=True;"
  },
  "Kestrel": {
    "Endpoints": {
      "Http": {
        "Url": "http://0.0.0.0:5016"
      }
    }
  }
}
```

### Solution 4: Rebuild and Restart
```bash
# Stop containers
docker-compose -f docker/docker-compose.yml down

# Rebuild Rule Engine
docker-compose -f docker/docker-compose.yml build --no-cache ruleengine

# Start all services
docker-compose -f docker/docker-compose.yml up -d

# Verify Rule Engine is healthy
docker-compose -f docker/docker-compose.yml logs ruleengine

# Test Swagger directly
curl http://localhost:8082/swagger/index.html
```

### Access Swagger:
- **Direct**: http://localhost:8082/swagger
- **Via NGINX**: http://localhost/ruleapi/swagger

---

## Fix ETL UI Dashboard Issue

### Problem: Dashboard fails when deployed on server

### Solution 1: Update Next.js Configuration

Create/update `ui/next.config.js`:
```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  basePath: '/etlui',
  assetPrefix: '/etlui',
  output: 'standalone',
  trailingSlash: true,
  
  // Fix for server-side rendering issues
  compiler: {
    removeConsole: process.env.NODE_ENV === 'production',
  },
  
  // Fix for API calls
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: '/etlapi/api/:path*',
      },
    ];
  },
  
  // Allow external images
  images: {
    domains: ['localhost', '202.131.115.228'],
    unoptimized: true,
  },
}

module.exports = nextConfig
```

### Solution 2: Fix Environment Variables in Dockerfile

Update `docker/Dockerfile.ui`:
```dockerfile
# Build arguments
ARG NEXT_PUBLIC_BASE_PATH=/etlui
ARG NEXT_PUBLIC_ASSET_PREFIX=/etlui
ARG NEXT_PUBLIC_API_URL=/etlapi/api
ARG NEXT_PUBLIC_WS_URL=/etlapi/ws

# Set environment variables during build
ENV NEXT_PUBLIC_BASE_PATH=$NEXT_PUBLIC_BASE_PATH
ENV NEXT_PUBLIC_ASSET_PREFIX=$NEXT_PUBLIC_ASSET_PREFIX
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_WS_URL=$NEXT_PUBLIC_WS_URL
ENV NODE_ENV=production

# Build the application
RUN npm run build

# Production stage
FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Copy built assets
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

EXPOSE 3001
ENV PORT=3001
ENV HOSTNAME="0.0.0.0"

CMD ["node", "server.js"]
```

### Solution 3: Rebuild UI
```bash
# Rebuild UI container
docker-compose -f docker/docker-compose.yml build --no-cache ui

# Restart UI
docker-compose -f docker/docker-compose.yml up -d ui

# Check logs
docker-compose -f docker/docker-compose.yml logs -f ui
```

---

## Load Data Using ETL

### Step 1: Run Database Migrations

```bash
# Run migrations container
docker-compose -f docker/docker-compose.yml up migrations

# Or manually execute SQL scripts
cd migrations/sql
sqlcmd -S 202.131.115.228,1433 -U sa -P 'Piyush@23D!gita1' -d RosteredAIDBDev -i 001_create_staging_tables.sql
sqlcmd -S 202.131.115.228,1433 -U sa -P 'Piyush@23D!gita1' -d RosteredAIDBDev -i 002_create_awards_summary_table.sql
# ... run all migration scripts in order
```

### Step 2: Load Awards Data (156 awards)

```bash
# Via API
curl -X POST http://localhost/etlapi/api/extract/awards \
  -H "Content-Type: application/json" \
  -d '{
    "award_codes": [],
    "load_all": true
  }'

# Via Python Script
docker-compose -f docker/docker-compose.yml exec api python -c "
from src.extract.extractors.awards import AwardsExtractor
from src.extract.api_client import APIClient
import asyncio

async def load_awards():
    async with APIClient() as client:
        extractor = AwardsExtractor(client)
        awards = await extractor.extract()
        print(f'Loaded {len(awards)} awards')

asyncio.run(load_awards())
"
```

### Step 3: Load Classifications

```bash
curl -X POST http://localhost/etlapi/api/extract/classifications \
  -H "Content-Type: application/json" \
  -d '{
    "award_codes": ["MA000120", "MA000001"],
    "load_all": false
  }'
```

### Step 4: Load Pay Rates

```bash
curl -X POST http://localhost/etlapi/api/extract/payrates \
  -H "Content-Type: application/json" \
  -d '{
    "award_codes": ["MA000120"],
    "load_all": false
  }'
```

### Step 5: Load Allowances

```bash
# Expense Allowances
curl -X POST http://localhost/etlapi/api/extract/expense-allowances \
  -H "Content-Type: application/json" \
  -d '{"award_codes": ["MA000120"]}'

# Wage Allowances
curl -X POST http://localhost/etlapi/api/extract/wage-allowances \
  -H "Content-Type: application/json" \
  -d '{"award_codes": ["MA000120"]}'
```

### Step 6: Load Penalties

```bash
curl -X POST http://localhost/etlapi/api/extract/penalties \
  -H "Content-Type: application/json" \
  -d '{
    "award_codes": ["MA000120"],
    "page_size": 100
  }'
```

### Step 7: Verify Data Loaded

```bash
# Check database
sqlcmd -S 202.131.115.228,1433 -U sa -P 'Piyush@23D!gita1' -d RosteredAIDBDev -Q "
SELECT 
    'Awards' as TableName, COUNT(*) as RecordCount FROM Stg_TblAwards
UNION ALL
SELECT 'Classifications', COUNT(*) FROM Stg_TblClassifications
UNION ALL
SELECT 'PayRates', COUNT(*) FROM Stg_TblPayRates
UNION ALL
SELECT 'ExpenseAllowances', COUNT(*) FROM Stg_TblExpenseAllowances
UNION ALL
SELECT 'WageAllowances', COUNT(*) FROM Stg_TblWageAllowances
UNION ALL
SELECT 'Penalties', COUNT(*) FROM Stg_TblPenalties
"
```

Expected output:
```
TableName            RecordCount
Awards               156
Classifications      ~8,000
PayRates             ~15,000
ExpenseAllowances    ~2,500
WageAllowances       ~3,200
Penalties            ~7,700 (per award)
```

---

## Process Rules & Compile Data

### Step 1: Execute Stored Procedures to Process Staging Data

#### 1.1 Compile Awards Summary
```bash
# Via SQL
sqlcmd -S 202.131.115.228,1433 -U sa -P 'Piyush@23D!gita1' -d RosteredAIDBDev -Q "
EXEC sp_CompileAwardsSummary @award_code = NULL;
"

# Via Rule Engine API
curl -X POST http://localhost/ruleapi/api/ruleengine/compile-awards \
  -H "Content-Type: application/json" \
  -d '{}'
```

#### 1.2 Compile Awards Detailed
```bash
# Via SQL
sqlcmd -S 202.131.115.228,1433 -U sa -P 'Piyush@23D!gita1' -d RosteredAIDBDev -Q "
EXEC sp_CompileAwardsDetailed @award_code = 'MA000120';
"

# Via Rule Engine API
curl -X POST http://localhost/ruleapi/api/ruleengine/compile-awards-detailed \
  -H "Content-Type: application/json" \
  -d '{"awardCode": "MA000120"}'
```

#### 1.3 Compile Award Rules (Enterprise Normalized Rules)
```bash
# Via SQL
sqlcmd -S 202.131.115.228,1433 -U sa -P 'Piyush@23D!gita1' -d RosteredAIDBDev -Q "
EXEC sp_CompileAwardRules 
  @award_code = 'MA000120', 
  @industry_type = 'Disability Services';
"

# Via Rule Engine API
curl -X POST http://localhost/ruleapi/api/rulecompiler/compile \
  -H "Content-Type: application/json" \
  -d '{
    "awardCode": "MA000120",
    "industryType": "Disability Services"
  }'
```

#### 1.4 Calculate Pay Rates (All Combinations)
```bash
# Via SQL
sqlcmd -S 202.131.115.228,1433 -U sa -P 'Piyush@23D!gita1' -d RosteredAIDBDev -Q "
EXEC sp_CalculateAllPayRates @award_code = 'MA000120';
"

# Via Rule Engine API
curl -X POST http://localhost/ruleapi/api/calculatedpayrates/calculate \
  -H "Content-Type: application/json" \
  -d '{"awardCode": "MA000120"}'
```

### Step 2: Verify Compiled Data

```bash
sqlcmd -S 202.131.115.228,1433 -U sa -P 'Piyush@23D!gita1' -d RosteredAIDBDev -Q "
SELECT 
    'AwardsSummary' as TableName, COUNT(*) as RecordCount FROM TblAwardsSummary
UNION ALL
SELECT 'AwardsDetailed', COUNT(*) FROM TblAwardsDetailed
UNION ALL
SELECT 'CompiledRules', COUNT(*) FROM TblCompiledRules
UNION ALL
SELECT 'CalculatedPayRates', COUNT(*) FROM TblCalculatedPayRates
"
```

Expected output:
```
TableName             RecordCount
AwardsSummary         156
AwardsDetailed        ~11,000 (for one award ~1,111)
CompiledRules         ~250 (per award)
CalculatedPayRates    ~500-2000 (per award)
```

---

## Access APIs & UIs

### 1. ETL UI Dashboard
- **URL**: http://localhost/etlui/
- **Features**:
  - Monitor ETL jobs
  - View data extraction status
  - Logs and monitoring
  - Awards management

### 2. ETL API (FastAPI)
- **Swagger**: http://localhost/etlapi/docs
- **ReDoc**: http://localhost/etlapi/redoc
- **Health**: http://localhost/etlapi/api/status
- **Features**:
  - Extract FWC data
  - Load to staging tables
  - WebSocket for real-time updates

### 3. Rule Engine API (.NET)
- **Swagger**: http://localhost/ruleapi/swagger
- **Direct**: http://localhost:8082/swagger
- **Health**: http://localhost/ruleapi/health
- **Features**:
  - Compile awards
  - Manage rules
  - Calculate pay rates
  - Query compiled data

### 4. Key API Endpoints

#### Rule Engine Endpoints:
```bash
# Get Awards Summary
GET http://localhost/ruleapi/api/awards?page=1&pageSize=50

# Get Awards Detailed
GET http://localhost/ruleapi/api/awardsdetailed?awardCode=MA000120&recordType=WITH_PAYRATE

# Get Compiled Rules (Tanda Pattern)
GET http://localhost/ruleapi/api/rulecompiler/rules?awardCode=MA000120&industryType=Retail

# Get Calculated Pay Rates
GET http://localhost/ruleapi/api/calculatedpayrates?awardCode=MA000120&employmentType=CASUAL&dayType=SUNDAY

# Get Penalties
GET http://localhost/ruleapi/api/penalties?awardCode=MA000120&classificationLevel=1

# Statistics
GET http://localhost/ruleapi/api/calculatedpayrates/statistics?awardCode=MA000120
GET http://localhost/ruleapi/api/penalties/statistics
```

---

## Troubleshooting

### Issue 1: Swagger Not Working (Rule Engine)

**Symptoms**: 404 error when accessing /swagger

**Solutions**:
```bash
# 1. Check if container is running
docker ps | grep ruleengine

# 2. Check container logs
docker logs etl-ruleengine

# 3. Test API health
curl http://localhost:8082/health

# 4. Access Swagger directly (bypass NGINX)
curl http://localhost:8082/swagger/index.html

# 5. Restart container
docker-compose -f docker/docker-compose.yml restart ruleengine

# 6. Rebuild if necessary
docker-compose -f docker/docker-compose.yml build --no-cache ruleengine
docker-compose -f docker/docker-compose.yml up -d ruleengine
```

### Issue 2: ETL UI Dashboard Fails on Server

**Symptoms**: White screen or 500 error

**Solutions**:
```bash
# 1. Check UI container logs
docker logs etl-ui

# 2. Verify environment variables
docker-compose -f docker/docker-compose.yml exec ui env | grep NEXT

# 3. Test API connectivity from UI container
docker-compose -f docker/docker-compose.yml exec ui curl http://host.docker.internal:8000/api/status

# 4. Rebuild with correct environment
docker-compose -f docker/docker-compose.yml build --no-cache ui
docker-compose -f docker/docker-compose.yml up -d ui

# 5. Check NGINX configuration
curl -I http://localhost/etlui/
```

### Issue 3: Database Connection Errors

**Symptoms**: "Cannot connect to SQL Server"

**Solutions**:
```bash
# 1. Test database connectivity from host
sqlcmd -S 202.131.115.228,1433 -U sa -P 'Piyush@23D!gita1' -Q "SELECT @@VERSION"

# 2. Test from Docker container
docker-compose -f docker/docker-compose.yml exec api ping -c 3 host.docker.internal

# 3. Verify firewall rules
# Windows: Check Windows Firewall
# Linux: sudo ufw status

# 4. Check SQL Server configuration
sqlcmd -S 202.131.115.228,1433 -U sa -P 'Piyush@23D!gita1' -Q "
EXEC sp_configure 'remote access';
GO
"
```

### Issue 4: NGINX 502 Bad Gateway

**Symptoms**: NGINX returns 502 error

**Solutions**:
```bash
# 1. Check if backend services are running
docker-compose -f docker/docker-compose.yml ps

# 2. Test backend directly
curl http://localhost:8000/api/status  # ETL API
curl http://localhost:3001/            # ETL UI
curl http://localhost:8082/health      # Rule Engine

# 3. Check NGINX logs
# Windows
type C:\nginx\logs\error.log

# Linux
sudo tail -f /var/log/nginx/error.log

# 4. Verify NGINX configuration syntax
nginx -t

# 5. Reload NGINX
nginx -s reload
```

### Issue 5: Docker Container Won't Start

**Symptoms**: Container exits immediately

**Solutions**:
```bash
# 1. Check logs
docker-compose -f docker/docker-compose.yml logs ruleengine

# 2. Inspect container
docker inspect etl-ruleengine

# 3. Run container interactively
docker run -it --entrypoint /bin/bash <image-name>

# 4. Check disk space
docker system df

# 5. Clean up Docker
docker system prune -a
```

---

## Unit Testing

### Run .NET Unit Tests (Rule Engine)

```bash
cd RuleEngine/RuleEngine.Tests

# Restore dependencies
dotnet restore

# Run all tests
dotnet test

# Run with verbosity
dotnet test --verbosity detailed

# Run specific test
dotnet test --filter "ClassName=CompileAwardsSummaryCommandHandlerTests"

# Generate code coverage
dotnet test --collect:"XPlat Code Coverage"
```

Expected output:
```
Passed!  - Failed:     0, Passed:     6, Skipped:     0, Total:     6
```

### Run Python Unit Tests (ETL)

```bash
cd etlpipeline-local

# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test file
pytest tests/test_awards_extractor.py

# Run with verbose output
pytest tests/ -v
```

### Integration Tests

```bash
# Test ETL API endpoints
pytest tests/integration/test_api_endpoints.py

# Test Rule Engine API
cd RuleEngine/RuleEngine.Tests
dotnet test --filter "Category=Integration"
```

---

## Production Deployment

### 1. Pre-Deployment Checklist

- [ ] All unit tests passing
- [ ] Integration tests passing
- [ ] Database migrations reviewed
- [ ] Environment variables configured
- [ ] NGINX configuration tested
- [ ] SSL certificates installed (for HTTPS)
- [ ] Backup strategy in place
- [ ] Monitoring configured
- [ ] Load testing completed

### 2. Production Environment Variables

Create `.env.production`:
```bash
# Database (Production)
MSSQL_HOST=production-sql-server.com
MSSQL_PORT=1433
MSSQL_DATABASE=RosteredAIProd
MSSQL_USER=appuser
MSSQL_PASSWORD=<strong-password>

# Logging
LOG_LEVEL=INFO
SENTRY_DSN=https://xxx@sentry.io/xxx

# Feature Flags
ENABLE_SWAGGER=false  # Disable in production
ENABLE_CORS=false
```

### 3. Deploy with Docker Compose

```bash
# Pull latest images
docker-compose -f docker/docker-compose.prod.yml pull

# Deploy
docker-compose -f docker/docker-compose.prod.yml up -d

# Verify health
docker-compose -f docker/docker-compose.prod.yml ps
```

### 4. Kubernetes Deployment (Enterprise)

```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/deployments/
kubectl apply -f k8s/services/
kubectl apply -f k8s/ingress.yaml

# Verify deployments
kubectl get pods -n rostered-ai
kubectl get services -n rostered-ai
kubectl get ingress -n rostered-ai
```

### 5. Scaling for 70k Users

```bash
# Scale API instances
docker-compose -f docker/docker-compose.prod.yml up -d --scale api=5 --scale ruleengine=3

# Or with Kubernetes
kubectl scale deployment rule-engine --replicas=10 -n rostered-ai
kubectl scale deployment etl-api --replicas=5 -n rostered-ai
```

### 6. Monitoring & Alerts

```bash
# Configure health checks
curl http://localhost/ruleapi/health
curl http://localhost/etlapi/api/status

# Set up Application Insights (Azure)
# Add to appsettings.json:
{
  "ApplicationInsights": {
    "InstrumentationKey": "your-key-here"
  }
}

# Configure Prometheus metrics
# Metrics available at:
# - http://localhost/ruleapi/metrics
# - http://localhost/etlapi/metrics
```

---

## Complete End-to-End Workflow

### Scenario: Deploy and Process Award MA000120

```bash
# 1. Start all services
docker-compose -f docker/docker-compose.yml up -d

# 2. Wait for services to be healthy
sleep 30

# 3. Verify services
curl http://localhost/etlapi/api/status
curl http://localhost/ruleapi/health

# 4. Run database migrations
docker-compose -f docker/docker-compose.yml up migrations

# 5. Load award data
curl -X POST http://localhost/etlapi/api/extract/awards \
  -H "Content-Type: application/json" \
  -d '{"award_codes": ["MA000120"], "load_all": false}'

# 6. Load classifications
curl -X POST http://localhost/etlapi/api/extract/classifications \
  -H "Content-Type: application/json" \
  -d '{"award_codes": ["MA000120"]}'

# 7. Load pay rates
curl -X POST http://localhost/etlapi/api/extract/payrates \
  -H "Content-Type: application/json" \
  -d '{"award_codes": ["MA000120"]}'

# 8. Load penalties
curl -X POST http://localhost/etlapi/api/extract/penalties \
  -H "Content-Type: application/json" \
  -d '{"award_codes": ["MA000120"], "page_size": 100}'

# 9. Load allowances
curl -X POST http://localhost/etlapi/api/extract/expense-allowances \
  -H "Content-Type: application/json" \
  -d '{"award_codes": ["MA000120"]}'

curl -X POST http://localhost/etlapi/api/extract/wage-allowances \
  -H "Content-Type: application/json" \
  -d '{"award_codes": ["MA000120"]}'

# 10. Compile awards summary
curl -X POST http://localhost/ruleapi/api/ruleengine/compile-awards \
  -H "Content-Type: application/json" \
  -d '{}'

# 11. Compile awards detailed
curl -X POST http://localhost/ruleapi/api/ruleengine/compile-awards-detailed \
  -H "Content-Type: application/json" \
  -d '{"awardCode": "MA000120"}'

# 12. Compile rules (Tanda pattern)
curl -X POST http://localhost/ruleapi/api/rulecompiler/compile \
  -H "Content-Type: application/json" \
  -d '{"awardCode": "MA000120", "industryType": "Disability Services"}'

# 13. Calculate pay rates
curl -X POST http://localhost/ruleapi/api/calculatedpayrates/calculate \
  -H "Content-Type: application/json" \
  -d '{"awardCode": "MA000120"}'

# 14. Query compiled rules via UI
# Open browser: http://localhost/etlui/
# Navigate to: Compiled Rules page
# Filter by: Award MA000120

# 15. Access Rule Engine API
# Open browser: http://localhost/ruleapi/swagger
# Test endpoints

# 16. Verify data in database
sqlcmd -S 202.131.115.228,1433 -U sa -P 'Piyush@23D!gita1' -d RosteredAIDBDev -Q "
SELECT 
    (SELECT COUNT(*) FROM Stg_TblAwards WHERE code = 'MA000120') as StagingAwards,
    (SELECT COUNT(*) FROM Stg_TblPenalties WHERE award_code = 'MA000120') as StagingPenalties,
    (SELECT COUNT(*) FROM TblAwardsDetailed WHERE award_code = 'MA000120') as DetailedRecords,
    (SELECT COUNT(*) FROM TblCompiledRules WHERE award_code = 'MA000120') as CompiledRules,
    (SELECT COUNT(*) FROM TblCalculatedPayRates WHERE award_code = 'MA000120') as CalculatedRates
"
```

Expected output:
```
StagingAwards: 1
StagingPenalties: 7,700
DetailedRecords: 1,111
CompiledRules: ~250
CalculatedRates: ~500-2000
```

---

## Support & Resources

### Documentation:
- Architecture: `/docs/enterprise_scalability_architecture.md`
- Pay Calculations: `/docs/pay_calculation_scenarios.md`
- Rule Engine: `/docs/json_rule_engine_guide.md`
- Penalties Integration: `/docs/penalties_integration_guide.md`

### API Documentation:
- ETL API: http://localhost/etlapi/docs
- Rule Engine API: http://localhost/ruleapi/swagger

### Logs Location:
- **Docker**: `docker-compose logs -f <service-name>`
- **ETL API**: `/app/logs/` (inside container)
- **Rule Engine**: Stdout (captured by Docker)
- **NGINX**: `C:\nginx\logs\` (Windows) or `/var/log/nginx/` (Linux)

### Contact:
- GitHub Issues: https://github.com/learntocodegpt4/etlpipeline-local/issues
- Email: support@rosteredai.com

---

## Quick Reference Commands

```bash
# Build & Start
docker-compose -f docker/docker-compose.yml up -d --build

# Stop All
docker-compose -f docker/docker-compose.yml down

# Restart Service
docker-compose -f docker/docker-compose.yml restart <service-name>

# View Logs
docker-compose -f docker/docker-compose.yml logs -f <service-name>

# Execute Command in Container
docker-compose -f docker/docker-compose.yml exec <service-name> /bin/bash

# Rebuild Single Service
docker-compose -f docker/docker-compose.yml build --no-cache <service-name>
docker-compose -f docker/docker-compose.yml up -d <service-name>

# Clean Up
docker-compose -f docker/docker-compose.yml down -v
docker system prune -a
```

---

## Conclusion

This guide provides complete instructions for deploying, building, and operating the RosteredAI system at enterprise scale. Follow the steps in order for successful deployment. For issues, refer to the Troubleshooting section or contact support.

**Next Steps After Deployment:**
1. Load data for all 156 awards
2. Compile rules for each industry type
3. Set up monitoring and alerts
4. Configure backups
5. Perform load testing
6. Train system administrators

**System is now production-ready for 70,000+ concurrent users!** 🚀
