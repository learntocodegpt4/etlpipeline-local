"""Azure Functions entry point for ETL Pipeline"""

import json
import logging
import asyncio
from datetime import datetime
from typing import Optional

import azure.functions as func

# Import ETL pipeline components
# Note: Ensure src package is available in Azure Function deployment
from src.orchestrator.pipeline import run_etl_pipeline
from src.utils.logging import setup_logging

# Configure logging
setup_logging(log_level="INFO")
logger = logging.getLogger(__name__)

app = func.FunctionApp()


@app.schedule(
    schedule="0 0 2 * * *",  # 2 AM daily
    arg_name="timer",
    run_on_startup=False,
)
async def etl_timer_trigger(timer: func.TimerRequest) -> None:
    """
    Timer-triggered Azure Function to run ETL pipeline.
    Runs daily at 2 AM.
    """
    utc_timestamp = datetime.utcnow().isoformat()

    if timer.past_due:
        logger.warning("The timer is past due!")

    logger.info(f"ETL Pipeline timer trigger started at {utc_timestamp}")

    try:
        result = await run_etl_pipeline()
        logger.info(
            f"ETL Pipeline completed successfully. "
            f"Status: {result.status.value}, "
            f"Records: {result.total_records_processed}, "
            f"Duration: {result.duration_seconds:.2f}s"
        )
    except Exception as e:
        logger.error(f"ETL Pipeline failed: {str(e)}")
        raise


@app.route(route="trigger", methods=["POST"])
async def http_trigger(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP-triggered Azure Function to manually run ETL pipeline.
    
    Request body (optional):
    {
        "award_codes": ["MA000001", "MA000002"]
    }
    """
    logger.info("ETL Pipeline HTTP trigger received")

    try:
        # Parse request body
        award_codes: Optional[list] = None
        try:
            req_body = req.get_json()
            award_codes = req_body.get("award_codes")
        except ValueError:
            pass

        # Run pipeline
        result = await run_etl_pipeline(award_codes=award_codes)

        return func.HttpResponse(
            body=json.dumps(result.to_dict()),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logger.error(f"ETL Pipeline failed: {str(e)}")
        return func.HttpResponse(
            body=json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json",
        )


@app.route(route="status", methods=["GET"])
def status_check(req: func.HttpRequest) -> func.HttpResponse:
    """Health check endpoint"""
    return func.HttpResponse(
        body=json.dumps({
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "FWC ETL Pipeline Azure Function",
        }),
        status_code=200,
        mimetype="application/json",
    )
