"""Rerun ETL for a single award and print results.

Usage:
    python scripts\rerun_award.py AWARD_CODE

This script:
- Initializes state manager
- Optionally deletes previous jobs for the same award_code (best-effort)
- Runs the ETL for that single award
- Prints pipeline step results and summary
"""
import asyncio
import sys
import sqlite3
from typing import Optional

from src.orchestrator.pipeline import ETLPipeline
from src.orchestrator.state_manager import StateManager
from src.utils.logging import setup_logging, get_logger
from src.config.settings import get_settings

logger = get_logger(__name__)


def delete_previous_jobs_for_award(award_code: str) -> None:
    """Best-effort: remove job entries that mention the award_code in job_steps.details or metadata.
    This uses the local SQLite state DB.
    """
    db = "data/state.db"
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    # Try to find job_ids with award_code in job_steps.details
    try:
        cur.execute("SELECT job_id FROM job_steps WHERE details LIKE ?", (f"%{award_code}%",))
        rows = cur.fetchall()
        job_ids = {r[0] for r in rows}
        if not job_ids:
            print(f"No previous job steps found referencing award '{award_code}'")
            return
        print(f"Found previous jobs referencing award '{award_code}': {job_ids}. Removing those rows from job_steps and jobs (best-effort).")
        for jid in job_ids:
            cur.execute("DELETE FROM job_steps WHERE job_id = ?", (jid,))
            cur.execute("DELETE FROM jobs WHERE job_id = ?", (jid,))
        conn.commit()
        print("Deleted previous job records (best-effort).")
    except Exception as e:
        print("Error while cleaning state DB:", e)
    finally:
        conn.close()


async def run_for_award(award_code: str) -> None:
    settings = get_settings()
    setup_logging(log_level=settings.log_level, log_file=settings.log_file_path)

    logger.info("rerun_award_starting", award=award_code)

    # Initialize state manager
    state_manager = StateManager()
    await state_manager.initialize()

    # Build pipeline and run single award
    pipeline = ETLPipeline(award_codes=[award_code])

    try:
        result = await pipeline.run()
        print("Pipeline completed:")
        print(result.to_dict())
    except Exception as e:
        print("Pipeline run failed:", e)


def main(argv: Optional[list] = None) -> None:
    argv = argv or sys.argv[1:]
    if not argv:
        print("Usage: python scripts\\rerun_award.py AWARD_CODE")
        sys.exit(2)
    award_code = argv[0]

    # Best-effort cleanup of previous jobs for that award
    try:
        delete_previous_jobs_for_award(award_code)
    except Exception as e:
        print("Warning: could not clean previous jobs:", e)

    asyncio.run(run_for_award(award_code))


if __name__ == "__main__":
    main()
