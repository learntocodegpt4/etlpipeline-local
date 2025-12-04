"""ETL Pipeline Orchestrator.

Coordinates the execution of multiple ETL pipelines for different
FWC API endpoints.
"""

from datetime import datetime
from typing import Any

import structlog

from src.config.settings import get_settings
from src.core.interfaces import PipelineContext
from src.core.pipeline import Pipeline, PipelineBuilder
from src.extract.extractors import (
    AwardsExtractor,
    ClassificationsExtractor,
    ExpenseAllowancesExtractor,
    PayRatesExtractor,
    WageAllowancesExtractor,
)
from src.load.bulk_loader import BulkLoader
from src.load.sql_connector import SQLConnector
from src.orchestrator.state_manager import StateManager
from src.transform.transformers import (
    AwardsTransformer,
    ClassificationsTransformer,
    ExpenseAllowancesTransformer,
    PayRatesTransformer,
    WageAllowancesTransformer,
)
from src.utils.helpers import generate_job_id

logger = structlog.get_logger(__name__)


class ETLOrchestrator:
    """Orchestrates the complete ETL process for FWC data.

    Manages the execution of pipelines for:
    - Awards
    - Classifications (per award)
    - Pay Rates (per award)
    - Expense Allowances (per award)
    - Wage Allowances (per award)
    """

    def __init__(
        self,
        connector: SQLConnector | None = None,
        state_manager: StateManager | None = None,
    ):
        self.settings = get_settings()
        self.connector = connector or SQLConnector()
        self.state_manager = state_manager or StateManager()
        self._logger = logger.bind(component="etl_orchestrator")

    def _create_awards_pipeline(self) -> Pipeline:
        """Create pipeline for awards extraction."""
        return (
            PipelineBuilder("awards_pipeline")
            .with_extractor(AwardsExtractor())
            .with_transformer(AwardsTransformer())
            .with_loader(
                BulkLoader(
                    connector=self.connector,
                    table_name="awards",
                    key_columns=["award_fixed_id", "published_year"],
                )
            )
            .build()
        )

    def _create_classifications_pipeline(self) -> Pipeline:
        """Create pipeline for classifications extraction."""
        return (
            PipelineBuilder("classifications_pipeline")
            .with_extractor(ClassificationsExtractor())
            .with_transformer(ClassificationsTransformer())
            .with_loader(
                BulkLoader(
                    connector=self.connector,
                    table_name="classifications",
                    key_columns=["classification_fixed_id", "award_code", "published_year"],
                )
            )
            .build()
        )

    def _create_pay_rates_pipeline(self) -> Pipeline:
        """Create pipeline for pay rates extraction."""
        return (
            PipelineBuilder("pay_rates_pipeline")
            .with_extractor(PayRatesExtractor())
            .with_transformer(PayRatesTransformer())
            .with_loader(
                BulkLoader(
                    connector=self.connector,
                    table_name="pay_rates",
                    key_columns=["classification_fixed_id", "award_code", "operative_from"],
                )
            )
            .build()
        )

    def _create_expense_allowances_pipeline(self) -> Pipeline:
        """Create pipeline for expense allowances extraction."""
        return (
            PipelineBuilder("expense_allowances_pipeline")
            .with_extractor(ExpenseAllowancesExtractor())
            .with_transformer(ExpenseAllowancesTransformer())
            .with_loader(
                BulkLoader(
                    connector=self.connector,
                    table_name="expense_allowances",
                    key_columns=["expense_allowance_fixed_id", "award_code", "operative_from"],
                )
            )
            .build()
        )

    def _create_wage_allowances_pipeline(self) -> Pipeline:
        """Create pipeline for wage allowances extraction."""
        return (
            PipelineBuilder("wage_allowances_pipeline")
            .with_extractor(WageAllowancesExtractor())
            .with_transformer(WageAllowancesTransformer())
            .with_loader(
                BulkLoader(
                    connector=self.connector,
                    table_name="wage_allowances",
                    key_columns=["wage_allowance_fixed_id", "award_code", "operative_from"],
                )
            )
            .build()
        )

    async def run_full_etl(
        self,
        award_codes: list[str] | None = None,
        job_id: str | None = None,
    ) -> dict[str, Any]:
        """Run the complete ETL process for all endpoints.

        Args:
            award_codes: Optional list of specific award codes to process
            job_id: Optional job ID (generated if not provided)

        Returns:
            Summary of the ETL execution
        """
        job_id = job_id or generate_job_id()
        start_time = datetime.now()

        self._logger.info(
            "full_etl_started",
            job_id=job_id,
            award_codes=award_codes,
        )

        # Track results
        results: dict[str, Any] = {
            "job_id": job_id,
            "started_at": start_time.isoformat(),
            "pipelines": {},
        }

        try:
            # Update job status
            await self.state_manager.create_job(job_id, "full_etl")

            # 1. Extract awards first
            self._logger.info("processing_awards")
            awards_pipeline = self._create_awards_pipeline()
            awards_context = await awards_pipeline.run(job_id=f"{job_id}_awards")

            results["pipelines"]["awards"] = self._summarize_context(awards_context)

            # Get award codes to process
            if not award_codes:
                award_codes = self._extract_award_codes(awards_context)

            self._logger.info(
                "awards_processed",
                total_awards=len(award_codes),
            )

            # 2. Process award-specific data for each award
            for award_code in award_codes:
                self._logger.info("processing_award", award_code=award_code)

                # Classifications
                try:
                    classifications_context = await self._create_classifications_pipeline().run(
                        params={"award_code": award_code},
                        job_id=f"{job_id}_classifications_{award_code}",
                    )
                    results["pipelines"].setdefault("classifications", {})[
                        award_code
                    ] = self._summarize_context(classifications_context)
                except Exception as e:
                    self._logger.error(
                        "classifications_failed",
                        award_code=award_code,
                        error=str(e),
                    )

                # Pay Rates
                try:
                    pay_rates_context = await self._create_pay_rates_pipeline().run(
                        params={"award_code": award_code},
                        job_id=f"{job_id}_pay_rates_{award_code}",
                    )
                    results["pipelines"].setdefault("pay_rates", {})[
                        award_code
                    ] = self._summarize_context(pay_rates_context)
                except Exception as e:
                    self._logger.error(
                        "pay_rates_failed",
                        award_code=award_code,
                        error=str(e),
                    )

                # Expense Allowances
                try:
                    expense_context = await self._create_expense_allowances_pipeline().run(
                        params={"award_code": award_code},
                        job_id=f"{job_id}_expense_allowances_{award_code}",
                    )
                    results["pipelines"].setdefault("expense_allowances", {})[
                        award_code
                    ] = self._summarize_context(expense_context)
                except Exception as e:
                    self._logger.error(
                        "expense_allowances_failed",
                        award_code=award_code,
                        error=str(e),
                    )

                # Wage Allowances
                try:
                    wage_context = await self._create_wage_allowances_pipeline().run(
                        params={"award_code": award_code},
                        job_id=f"{job_id}_wage_allowances_{award_code}",
                    )
                    results["pipelines"].setdefault("wage_allowances", {})[
                        award_code
                    ] = self._summarize_context(wage_context)
                except Exception as e:
                    self._logger.error(
                        "wage_allowances_failed",
                        award_code=award_code,
                        error=str(e),
                    )

            # Update job status
            end_time = datetime.now()
            results["completed_at"] = end_time.isoformat()
            results["duration_seconds"] = (end_time - start_time).total_seconds()
            results["status"] = "success"

            await self.state_manager.update_job(
                job_id,
                status="success",
                completed_at=end_time,
            )

            self._logger.info(
                "full_etl_completed",
                job_id=job_id,
                duration=results["duration_seconds"],
            )

        except Exception as e:
            results["status"] = "failed"
            results["error"] = str(e)

            await self.state_manager.update_job(
                job_id,
                status="failed",
                error_message=str(e),
            )

            self._logger.exception(
                "full_etl_failed",
                job_id=job_id,
                error=str(e),
            )

        return results

    async def run_single_pipeline(
        self,
        pipeline_type: str,
        award_code: str | None = None,
        job_id: str | None = None,
    ) -> PipelineContext:
        """Run a single pipeline by type.

        Args:
            pipeline_type: Type of pipeline (awards, classifications, pay_rates, etc.)
            award_code: Award code (required for award-specific pipelines)
            job_id: Optional job ID

        Returns:
            Pipeline execution context
        """
        job_id = job_id or generate_job_id()

        pipeline_map = {
            "awards": self._create_awards_pipeline,
            "classifications": self._create_classifications_pipeline,
            "pay_rates": self._create_pay_rates_pipeline,
            "expense_allowances": self._create_expense_allowances_pipeline,
            "wage_allowances": self._create_wage_allowances_pipeline,
        }

        if pipeline_type not in pipeline_map:
            raise ValueError(f"Unknown pipeline type: {pipeline_type}")

        if pipeline_type != "awards" and not award_code:
            raise ValueError(f"award_code is required for {pipeline_type} pipeline")

        pipeline = pipeline_map[pipeline_type]()
        params = {"award_code": award_code} if award_code else {}

        return await pipeline.run(params=params, job_id=job_id)

    def _extract_award_codes(self, context: PipelineContext) -> list[str]:
        """Extract unique award codes from the awards context.

        Args:
            context: Pipeline context after awards extraction

        Returns:
            List of unique award codes
        """
        extract_result = context.get_step_result("extract")
        if not extract_result or not extract_result.data:
            return []

        codes = set()
        for record in extract_result.data:
            code = record.get("code")
            if code:
                codes.add(code)

        return list(codes)

    def _summarize_context(self, context: PipelineContext) -> dict[str, Any]:
        """Create a summary of the pipeline context.

        Args:
            context: Pipeline context

        Returns:
            Summary dictionary
        """
        summary: dict[str, Any] = {
            "job_id": context.job_id,
            "has_errors": context.has_errors,
            "steps": {},
        }

        for step_name, result in context.step_results.items():
            summary["steps"][step_name] = {
                "status": result.status.value,
                "records_processed": result.records_processed,
                "duration_seconds": result.duration_seconds,
                "error": result.error,
            }

        return summary
