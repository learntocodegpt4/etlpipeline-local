"""Main entry point for the FWC ETL Pipeline."""

import asyncio
from typing import Any

import structlog

from src.config.settings import get_settings
from src.orchestrator.pipeline import ETLOrchestrator
from src.orchestrator.scheduler import ETLScheduler
from src.utils.logging import setup_logging

logger = structlog.get_logger(__name__)


async def run_etl(
    award_codes: list[str] | None = None,
    pipeline_type: str | None = None,
) -> dict[str, Any]:
    """Run the ETL pipeline.

    Args:
        award_codes: Optional list of award codes to process
        pipeline_type: Optional specific pipeline type to run

    Returns:
        Pipeline execution results
    """
    orchestrator = ETLOrchestrator()

    if pipeline_type:
        # Run specific pipeline
        award_code = award_codes[0] if award_codes else None
        context = await orchestrator.run_single_pipeline(
            pipeline_type=pipeline_type,
            award_code=award_code,
        )
        return {
            "job_id": context.job_id,
            "status": "success" if not context.has_errors else "failed",
            "errors": context.errors,
        }
    else:
        # Run full ETL
        return await orchestrator.run_full_etl(award_codes=award_codes)


def run_scheduled() -> None:
    """Run the ETL pipeline with scheduler."""
    settings = get_settings()
    scheduler = ETLScheduler()
    orchestrator = ETLOrchestrator()

    scheduler.add_job(
        "scheduled_etl",
        orchestrator.run_full_etl,
        cron_expression=settings.scheduler_cron_expression,
    )

    logger.info(
        "scheduler_configured",
        cron=settings.scheduler_cron_expression,
    )

    scheduler.start()

    try:
        # Keep running
        asyncio.get_event_loop().run_forever()
    except (KeyboardInterrupt, SystemExit):
        scheduler.stop()
        logger.info("scheduler_stopped")


def main() -> None:
    """Main entry point."""
    setup_logging()
    logger.info("etl_pipeline_starting")

    # Parse command line arguments
    import argparse

    parser = argparse.ArgumentParser(description="FWC ETL Pipeline")
    parser.add_argument(
        "--mode",
        choices=["run", "schedule", "api"],
        default="run",
        help="Execution mode: run (once), schedule (cron), api (server)",
    )
    parser.add_argument(
        "--pipeline",
        choices=["awards", "classifications", "pay_rates", "expense_allowances", "wage_allowances"],
        help="Specific pipeline to run (optional)",
    )
    parser.add_argument(
        "--award-codes",
        nargs="*",
        help="Specific award codes to process (optional)",
    )
    parser.add_argument(
        "--migrate",
        action="store_true",
        help="Run database migrations before ETL",
    )

    args = parser.parse_args()

    # Run migrations if requested
    if args.migrate:
        from src.load.sql_connector import SQLConnector

        logger.info("running_migrations")
        connector = SQLConnector()
        connector.run_migrations()

    if args.mode == "run":
        # Run ETL once
        result = asyncio.run(
            run_etl(
                award_codes=args.award_codes,
                pipeline_type=args.pipeline,
            )
        )
        logger.info("etl_completed", result=result)

    elif args.mode == "schedule":
        # Run with scheduler
        run_scheduled()

    elif args.mode == "api":
        # Run API server
        from src.api.app import run_server

        run_server()


if __name__ == "__main__":
    main()
