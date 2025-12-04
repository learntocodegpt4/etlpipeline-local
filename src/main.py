"""Main entry point for ETL Pipeline"""

import asyncio
import argparse
import sys
from typing import Optional, List

from src.config.settings import get_settings
from src.utils.logging import setup_logging, get_logger
from src.orchestrator.pipeline import run_etl_pipeline
from src.orchestrator.state_manager import StateManager


def main() -> None:
    """Main entry point"""
    parser = argparse.ArgumentParser(description="FWC Modern Awards ETL Pipeline")
    parser.add_argument(
        "--mode",
        choices=["run", "api", "schedule"],
        default="run",
        help="Execution mode (default: run)",
    )
    parser.add_argument(
        "--awards",
        nargs="*",
        help="Specific award codes to process (default: all)",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Log level",
    )

    args = parser.parse_args()

    # Setup logging
    settings = get_settings()
    log_level = args.log_level or settings.log_level
    setup_logging(log_level=log_level, log_file=settings.log_file_path)

    logger = get_logger(__name__)
    logger.info("etl_pipeline_starting", mode=args.mode)

    if args.mode == "run":
        # Run ETL pipeline once
        asyncio.run(run_pipeline(args.awards))

    elif args.mode == "api":
        # Start API server
        from src.api.app import run_server
        run_server()

    elif args.mode == "schedule":
        # Start with scheduler
        asyncio.run(run_with_scheduler())


async def run_pipeline(award_codes: Optional[List[str]] = None) -> None:
    """Run the ETL pipeline"""
    logger = get_logger(__name__)

    try:
        # Initialize state manager
        state_manager = StateManager()
        await state_manager.initialize()

        # Run pipeline
        result = await run_etl_pipeline(award_codes=award_codes)

        logger.info(
            "pipeline_completed",
            status=result.status.value,
            records=result.total_records_processed,
            duration=result.duration_seconds,
        )

        if result.errors:
            logger.warning("pipeline_had_errors", errors=result.errors)
            sys.exit(1)

    except Exception as e:
        logger.exception("pipeline_failed")
        sys.exit(1)


async def run_with_scheduler() -> None:
    """Run with scheduler enabled"""
    from src.orchestrator.scheduler import Scheduler

    logger = get_logger(__name__)
    settings = get_settings()

    # Initialize state manager
    state_manager = StateManager()
    await state_manager.initialize()

    # Create scheduler
    scheduler = Scheduler(run_job_func=run_etl_pipeline)

    if settings.etl_schedule_enabled:
        scheduler.add_cron_job()
        scheduler.start()
        logger.info("scheduler_started", cron=settings.etl_cron_expression)

        # Keep running
        try:
            while True:
                await asyncio.sleep(60)
        except KeyboardInterrupt:
            logger.info("scheduler_interrupted")
            scheduler.stop()
    else:
        logger.warning("scheduler_disabled")


if __name__ == "__main__":
    main()
