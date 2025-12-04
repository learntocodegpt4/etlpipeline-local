# Azure Migration Guide

This guide provides instructions for migrating the FWC ETL Pipeline to Azure cloud services.

## Migration Options

### Option 1: Azure Functions (Serverless)

Best for: Scheduled ETL jobs with varying workloads.

#### Architecture
```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Timer Trigger  │────>│  Azure Function │────>│  Azure SQL DB   │
│   (Schedule)    │     │   (ETL Logic)   │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │   FWC API       │
                        │                 │
                        └─────────────────┘
```

#### Setup Steps

1. **Create Azure Function App:**
   ```bash
   az functionapp create \
     --name fwc-etl-pipeline \
     --resource-group your-resource-group \
     --runtime python \
     --runtime-version 3.11 \
     --consumption-plan-location australiaeast \
     --storage-account yourstorageaccount
   ```

2. **Deploy the function:**
   ```bash
   cd azure
   func azure functionapp publish fwc-etl-pipeline
   ```

3. **Configure Application Settings:**
   ```bash
   az functionapp config appsettings set \
     --name fwc-etl-pipeline \
     --resource-group your-resource-group \
     --settings \
       FWC_API_BASE_URL="https://api.fwc.gov.au/api/v1" \
       FWC_API_KEY="@Microsoft.KeyVault(SecretUri=...)" \
       MSSQL_CONNECTION_STRING="@Microsoft.KeyVault(SecretUri=...)"
   ```

#### Function Code Structure

```python
# azure/function_app.py
import azure.functions as func
import logging
from src.orchestrator.pipeline import run_etl_pipeline

app = func.FunctionApp()

@app.schedule(schedule="0 0 2 * * *", arg_name="timer", run_on_startup=False)
async def etl_timer_trigger(timer: func.TimerRequest) -> None:
    """Run ETL pipeline on schedule (2 AM daily)"""
    logging.info("ETL Pipeline triggered by timer")
    
    try:
        result = await run_etl_pipeline()
        logging.info(f"ETL completed: {result.status.value}, records: {result.total_records_processed}")
    except Exception as e:
        logging.error(f"ETL failed: {str(e)}")
        raise

@app.route(route="trigger", methods=["POST"])
async def http_trigger(req: func.HttpRequest) -> func.HttpResponse:
    """Manually trigger ETL pipeline via HTTP"""
    logging.info("ETL Pipeline triggered via HTTP")
    
    try:
        result = await run_etl_pipeline()
        return func.HttpResponse(
            body=json.dumps(result.to_dict()),
            mimetype="application/json"
        )
    except Exception as e:
        return func.HttpResponse(
            body=json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )
```

### Option 2: Azure Container Instances (ACI)

Best for: Simple containerized deployment without orchestration.

#### Setup Steps

1. **Create Azure Container Registry:**
   ```bash
   az acr create \
     --name fwcetlregistry \
     --resource-group your-resource-group \
     --sku Basic
   ```

2. **Build and push Docker image:**
   ```bash
   # Login to ACR
   az acr login --name fwcetlregistry
   
   # Build and push
   docker build -t fwcetlregistry.azurecr.io/etl-pipeline:latest -f docker/Dockerfile .
   docker push fwcetlregistry.azurecr.io/etl-pipeline:latest
   ```

3. **Deploy container:**
   ```bash
   az container create \
     --name fwc-etl-pipeline \
     --resource-group your-resource-group \
     --image fwcetlregistry.azurecr.io/etl-pipeline:latest \
     --registry-login-server fwcetlregistry.azurecr.io \
     --registry-username <username> \
     --registry-password <password> \
     --ports 8000 \
     --environment-variables \
       FWC_API_BASE_URL=https://api.fwc.gov.au/api/v1 \
     --secure-environment-variables \
       FWC_API_KEY=<your-key> \
       MSSQL_CONNECTION_STRING=<your-connection-string>
   ```

### Option 3: Azure App Service

Best for: Web API with integrated monitoring and scaling.

#### Setup Steps

1. **Create App Service Plan:**
   ```bash
   az appservice plan create \
     --name fwc-etl-plan \
     --resource-group your-resource-group \
     --sku B1 \
     --is-linux
   ```

2. **Create Web App:**
   ```bash
   az webapp create \
     --name fwc-etl-api \
     --resource-group your-resource-group \
     --plan fwc-etl-plan \
     --runtime "PYTHON:3.11"
   ```

3. **Deploy from Docker:**
   ```bash
   az webapp config container set \
     --name fwc-etl-api \
     --resource-group your-resource-group \
     --docker-custom-image-name fwcetlregistry.azurecr.io/etl-pipeline:latest \
     --docker-registry-server-url https://fwcetlregistry.azurecr.io
   ```

### Option 4: Azure Virtual Machine

Best for: Full control over environment, similar to on-premises.

#### Setup Steps

1. **Create VM:**
   ```bash
   az vm create \
     --name fwc-etl-vm \
     --resource-group your-resource-group \
     --image Ubuntu2204 \
     --size Standard_B2s \
     --admin-username azureuser \
     --generate-ssh-keys
   ```

2. **Install Docker on VM:**
   ```bash
   ssh azureuser@<vm-ip>
   
   # Install Docker
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   
   # Clone repository
   git clone <your-repo> /opt/etlpipeline
   cd /opt/etlpipeline
   
   # Run with Docker Compose
   docker-compose -f docker/docker-compose.yml up -d
   ```

## Database Migration

### Azure SQL Database

1. **Create Azure SQL Database:**
   ```bash
   az sql server create \
     --name fwc-etl-sql-server \
     --resource-group your-resource-group \
     --location australiaeast \
     --admin-user sqladmin \
     --admin-password <password>
   
   az sql db create \
     --name etl_pipeline \
     --server fwc-etl-sql-server \
     --resource-group your-resource-group \
     --service-objective S0
   ```

2. **Run migrations:**
   ```bash
   # Using sqlcmd
   sqlcmd -S fwc-etl-sql-server.database.windows.net \
     -U sqladmin -P <password> \
     -d etl_pipeline \
     -i migrations/sql/001_create_base_tables.sql
   ```

3. **Update connection string:**
   ```
   MSSQL_CONNECTION_STRING=mssql+pyodbc://sqladmin:<password>@fwc-etl-sql-server.database.windows.net:1433/etl_pipeline?driver=ODBC+Driver+17+for+SQL+Server&Encrypt=yes
   ```

## Security Best Practices

### 1. Use Azure Key Vault for Secrets

```bash
# Create Key Vault
az keyvault create \
  --name fwc-etl-kv \
  --resource-group your-resource-group \
  --location australiaeast

# Store secrets
az keyvault secret set \
  --vault-name fwc-etl-kv \
  --name FWC-API-KEY \
  --value "<your-api-key>"

az keyvault secret set \
  --vault-name fwc-etl-kv \
  --name MSSQL-CONNECTION-STRING \
  --value "<your-connection-string>"
```

### 2. Configure Managed Identity

```bash
# Enable system-assigned identity
az webapp identity assign \
  --name fwc-etl-api \
  --resource-group your-resource-group

# Grant Key Vault access
az keyvault set-policy \
  --name fwc-etl-kv \
  --object-id <identity-object-id> \
  --secret-permissions get list
```

### 3. Use Private Endpoints

```bash
# Create private endpoint for SQL Database
az network private-endpoint create \
  --name fwc-etl-sql-pe \
  --resource-group your-resource-group \
  --vnet-name your-vnet \
  --subnet your-subnet \
  --private-connection-resource-id <sql-server-resource-id> \
  --group-id sqlServer \
  --connection-name fwc-etl-sql-connection
```

## Monitoring and Logging

### Application Insights

```bash
# Create Application Insights
az monitor app-insights component create \
  --app fwc-etl-insights \
  --resource-group your-resource-group \
  --location australiaeast

# Get instrumentation key
az monitor app-insights component show \
  --app fwc-etl-insights \
  --resource-group your-resource-group \
  --query instrumentationKey -o tsv
```

Add to application settings:
```
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=<key>;IngestionEndpoint=...
```

## Cost Optimization

### Recommendations

1. **Azure Functions (Consumption Plan)**: Pay only for execution time
2. **Azure SQL Serverless**: Auto-pause when not in use
3. **Reserved Instances**: Save up to 72% with 1-3 year commitments
4. **Schedule scaling**: Scale down during off-peak hours

### Sample Cost Estimate

| Service | SKU | Monthly Cost (AUD) |
|---------|-----|-------------------|
| Azure Functions | Consumption | ~$10-50 |
| Azure SQL | S0 | ~$25 |
| App Service | B1 | ~$20 |
| Storage | Standard | ~$5 |
| **Total** | | **~$60-100** |
