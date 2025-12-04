"""Azure Functions template for FWC ETL Pipeline.

This module provides Azure Functions integration for running the ETL pipeline
as serverless functions. It can be deployed to Azure Functions for scheduled
or HTTP-triggered execution.

To deploy:
1. Create an Azure Functions app with Python 3.11
2. Configure application settings with environment variables
3. Deploy this code along with the src/ package

Environment variables required:
- FWC_API_KEY: API key for FWC Modern Awards API
- MSSQL_HOST, MSSQL_DATABASE, MSSQL_USERNAME, MSSQL_PASSWORD: SQL Server connection
"""

import azure.functions as func
import asyncio
import json
import logging
from datetime import datetime

# Initialize function app
app = func.FunctionApp()


def get_orchestrator():
    """Get the ETL orchestrator instance."""
    # Import here to avoid circular imports and ensure proper initialization
    from src.orchestrator.pipeline import ETLOrchestrator
    return ETLOrchestrator()


@app.function_name(name="ScheduledETL")
@app.timer_trigger(
    schedule="0 0 2 * * *",  # Run at 2 AM UTC daily
    arg_name="timer",
    run_on_startup=False,
)
async def scheduled_etl(timer: func.TimerRequest) -> None:
    """Timer-triggered function for scheduled ETL runs.

    Runs the full ETL pipeline on a schedule defined by the cron expression.
    Default: Daily at 2 AM UTC.
    """
    logging.info("Scheduled ETL trigger started at %s", datetime.now().isoformat())

    if timer.past_due:
        logging.warning("Timer is past due!")

    try:
        orchestrator = get_orchestrator()
        result = await orchestrator.run_full_etl()

        logging.info("ETL completed: %s", json.dumps(result, default=str))

    except Exception as e:
        logging.exception("ETL failed: %s", str(e))
        raise


@app.function_name(name="HttpTriggerETL")
@app.route(route="etl/trigger", methods=["POST"])
async def http_trigger_etl(req: func.HttpRequest) -> func.HttpResponse:
    """HTTP-triggered function for manual ETL runs.

    Allows manual triggering of the ETL pipeline via HTTP request.

    Request body (optional):
    {
        "pipeline_type": "awards|classifications|pay_rates|expense_allowances|wage_allowances",
        "award_codes": ["MA000001", "MA000002"]
    }
    """
    logging.info("HTTP ETL trigger received")

    try:
        # Parse request body
        body = req.get_json() if req.get_body() else {}
        pipeline_type = body.get("pipeline_type")
        award_codes = body.get("award_codes")

        orchestrator = get_orchestrator()

        if pipeline_type:
            # Run specific pipeline
            award_code = award_codes[0] if award_codes else None
            context = await orchestrator.run_single_pipeline(
                pipeline_type=pipeline_type,
                award_code=award_code,
            )
            result = {
                "job_id": context.job_id,
                "status": "success" if not context.has_errors else "failed",
                "errors": context.errors,
            }
        else:
            # Run full ETL
            result = await orchestrator.run_full_etl(award_codes=award_codes)

        return func.HttpResponse(
            json.dumps(result, default=str),
            mimetype="application/json",
            status_code=200,
        )

    except Exception as e:
        logging.exception("ETL trigger failed: %s", str(e))
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500,
        )


@app.function_name(name="GetJobStatus")
@app.route(route="etl/jobs/{job_id}", methods=["GET"])
async def get_job_status(req: func.HttpRequest) -> func.HttpResponse:
    """Get the status of a specific ETL job.

    Path parameter:
    - job_id: The unique identifier of the job
    """
    job_id = req.route_params.get("job_id")

    if not job_id:
        return func.HttpResponse(
            json.dumps({"error": "job_id is required"}),
            mimetype="application/json",
            status_code=400,
        )

    try:
        from src.orchestrator.state_manager import StateManager

        state_manager = StateManager()
        job = await state_manager.get_job(job_id)

        if not job:
            return func.HttpResponse(
                json.dumps({"error": f"Job {job_id} not found"}),
                mimetype="application/json",
                status_code=404,
            )

        details = await state_manager.get_job_details(job_id)
        job["details"] = details

        return func.HttpResponse(
            json.dumps(job, default=str),
            mimetype="application/json",
            status_code=200,
        )

    except Exception as e:
        logging.exception("Failed to get job status: %s", str(e))
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500,
        )


@app.function_name(name="HealthCheck")
@app.route(route="health", methods=["GET"])
async def health_check(req: func.HttpRequest) -> func.HttpResponse:
    """Health check endpoint for the Azure Function."""
    from src.config.settings import get_settings

    settings = get_settings()

    health = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "environment": settings.environment,
        "function_app": True,
    }

    return func.HttpResponse(
        json.dumps(health),
        mimetype="application/json",
        status_code=200,
    )
