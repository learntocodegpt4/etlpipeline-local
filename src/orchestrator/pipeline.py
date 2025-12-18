"""ETL Pipeline orchestrator"""

import uuid
from typing import List, Optional
from datetime import datetime

from src.core.pipeline import Pipeline, PipelineContext, PipelineResult
from src.extract.api_client import APIClient
from src.extract.extractors import (
    AwardsExtractor,
    ClassificationsExtractor,
    PayRatesExtractor,
    ExpenseAllowancesExtractor,
    WageAllowancesExtractor,
    PenaltiesExtractor,
)
from src.transform.transformers import (
    AwardsTransformer,
    ClassificationsTransformer,
    PayRatesTransformer,
    ExpenseAllowancesTransformer,
    WageAllowancesTransformer,
    PenaltiesTransformer,
)
from src.load.bulk_loader import BulkLoader, RawDataLoader
from src.load.sql_connector import SQLConnector, get_connector
from src.orchestrator.state_manager import StateManager
from src.config.settings import get_settings
from src.utils.logging import get_logger

logger = get_logger(__name__)


class ETLPipeline:
    """Main ETL Pipeline orchestrator for FWC Modern Awards"""

    def __init__(
        self,
        api_client: Optional[APIClient] = None,
        connector: Optional[SQLConnector] = None,
        state_manager: Optional[StateManager] = None,
        award_codes: Optional[List[str]] = None,
    ):
        self.settings = get_settings()
        self.api_client = api_client
        self.connector = connector or get_connector()
        self.state_manager = state_manager or StateManager()
        self.award_codes = award_codes

        self._pipeline: Optional[Pipeline] = None

    async def _create_api_client(self) -> APIClient:
        """Create API client if not provided"""
        if self.api_client:
            return self.api_client
        return APIClient(
            base_url=self.settings.fwc_api_base_url,
            api_key=self.settings.fwc_api_key,
        )

    def _build_pipeline(self, api_client: APIClient) -> Pipeline:
        """Build the ETL pipeline with all steps"""
        pipeline = Pipeline(
            name="fwc_awards_etl",
            stop_on_error=True,
        )

        page_size = self.settings.default_page_size

        # Extract steps
        pipeline.add_step(AwardsExtractor(api_client, page_size))
        pipeline.add_step(ClassificationsExtractor(api_client, self.award_codes, page_size))
        pipeline.add_step(PayRatesExtractor(api_client, self.award_codes, page_size))
        pipeline.add_step(ExpenseAllowancesExtractor(api_client, self.award_codes, page_size))
        pipeline.add_step(WageAllowancesExtractor(api_client, self.award_codes, page_size))
        pipeline.add_step(PenaltiesExtractor(api_client, self.award_codes, page_size))

        # Transform steps
        pipeline.add_step(AwardsTransformer())
        pipeline.add_step(ClassificationsTransformer())
        pipeline.add_step(PayRatesTransformer())
        pipeline.add_step(ExpenseAllowancesTransformer())
        pipeline.add_step(WageAllowancesTransformer())
        pipeline.add_step(PenaltiesTransformer())

        # Load steps
        pipeline.add_step(BulkLoader(
            source_key="awards_transformer",
            table_name="Stg_TblAwards",
            key_columns=["award_id", "published_year"],
            connector=self.connector,
        ))
        pipeline.add_step(BulkLoader(
            source_key="classifications_transformer",
            table_name="Stg_TblClassifications",
            key_columns=["classification_fixed_id", "award_code", "published_year"],
            connector=self.connector,
        ))
        pipeline.add_step(BulkLoader(
            source_key="pay_rates_transformer",
            table_name="Stg_TblPayRates",
            key_columns=["classification_fixed_id", "award_code", "published_year"],
            connector=self.connector,
        ))
        pipeline.add_step(BulkLoader(
            source_key="expense_allowances_transformer",
            table_name="Stg_TblExpenseAllowances",
            key_columns=["expense_allowance_fixed_id", "award_code", "published_year"],
            connector=self.connector,
        ))
        pipeline.add_step(BulkLoader(
            source_key="wage_allowances_transformer",
            table_name="Stg_TblWageAllowances",
            key_columns=["wage_allowance_fixed_id", "award_code", "published_year"],
            connector=self.connector,
        ))
        pipeline.add_step(BulkLoader(
            source_key="penalties_transformer",
            table_name="Stg_TblPenalties",
            key_columns=["penalty_fixed_id", "award_code", "published_year"],
            connector=self.connector,
        ))

        return pipeline

    async def run(self, job_id: Optional[str] = None) -> PipelineResult:
        """Run the complete ETL pipeline"""
        job_id = job_id or str(uuid.uuid4())

        logger.info("etl_pipeline_starting", job_id=job_id)

        # Create job record with a descriptive name (pipeline + awards + timestamp)
        job_name = f"fwc_awards_etl:{','.join(self.award_codes) if self.award_codes else 'all'}:{datetime.utcnow().isoformat()}"
        await self.state_manager.create_job(job_id, name=job_name)

        # Update state
        await self.state_manager.update_job_status(job_id, "running")

        api_client = await self._create_api_client()

        try:
            async with api_client:
                pipeline = self._build_pipeline(api_client)
                context = PipelineContext(job_id=job_id)

                result = await pipeline.execute(context, job_id)

                # Save result to state
                await self.state_manager.save_job_result(job_id, result)

                return result

        except Exception as e:
            logger.exception("etl_pipeline_error", job_id=job_id)
            await self.state_manager.update_job_status(
                job_id, "failed", error_message=str(e)
            )
            raise

    async def run_single_award(
        self, award_code: str, job_id: Optional[str] = None
    ) -> PipelineResult:
        """Run ETL for a single award"""
        original_codes = self.award_codes
        self.award_codes = [award_code]
        try:
            return await self.run(job_id)
        finally:
            self.award_codes = original_codes


async def run_etl_pipeline(
    award_codes: Optional[List[str]] = None,
    job_id: Optional[str] = None,
) -> PipelineResult:
    """Convenience function to run ETL pipeline"""
    pipeline = ETLPipeline(award_codes=award_codes)
    return await pipeline.run(job_id)
