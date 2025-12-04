"""SQLAlchemy models for the FWC database."""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class Award(Base):
    """Award model for FWC awards."""

    __tablename__ = "awards"

    id = Column(Integer, primary_key=True, autoincrement=True)
    award_id = Column(Integer, nullable=False)
    award_fixed_id = Column(Integer, nullable=False)
    code = Column(String(50), nullable=False, index=True)
    name = Column(String(500), nullable=False)
    award_operative_from = Column(DateTime, nullable=True)
    award_operative_to = Column(DateTime, nullable=True)
    version_number = Column(Integer, nullable=True)
    last_modified_datetime = Column(DateTime, nullable=True)
    published_year = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        Index("ix_awards_award_fixed_id_published_year", "award_fixed_id", "published_year"),
    )


class Classification(Base):
    """Classification model for award classifications."""

    __tablename__ = "classifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    classification_fixed_id = Column(Integer, nullable=False)
    award_code = Column(String(50), nullable=False, index=True)
    classification = Column(String(500), nullable=True)
    classification_level = Column(Integer, nullable=True)
    parent_classification_name = Column(String(500), nullable=True)
    employee_rate_type_code = Column(String(50), nullable=True)
    operative_from = Column(DateTime, nullable=True)
    operative_to = Column(DateTime, nullable=True)
    version_number = Column(Integer, nullable=True)
    published_year = Column(Integer, nullable=True)
    last_modified_datetime = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        Index(
            "ix_classifications_award_code_classification_fixed_id",
            "award_code",
            "classification_fixed_id",
        ),
    )


class PayRate(Base):
    """Pay rate model for award pay rates."""

    __tablename__ = "pay_rates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    classification_fixed_id = Column(Integer, nullable=False)
    award_code = Column(String(50), nullable=False, index=True)
    base_pay_rate_id = Column(String(50), nullable=True)
    base_rate_type = Column(String(50), nullable=True)
    base_rate = Column(Float, nullable=True)
    calculated_pay_rate_id = Column(String(50), nullable=True)
    calculated_rate_type = Column(String(50), nullable=True)
    calculated_rate = Column(Float, nullable=True)
    parent_classification_name = Column(String(500), nullable=True)
    classification = Column(String(500), nullable=True)
    classification_level = Column(Integer, nullable=True)
    employee_rate_type_code = Column(String(50), nullable=True)
    operative_from = Column(DateTime, nullable=True)
    operative_to = Column(DateTime, nullable=True)
    version_number = Column(Integer, nullable=True)
    published_year = Column(Integer, nullable=True)
    last_modified_datetime = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        Index(
            "ix_pay_rates_award_code_classification_fixed_id",
            "award_code",
            "classification_fixed_id",
        ),
    )


class ExpenseAllowance(Base):
    """Expense allowance model."""

    __tablename__ = "expense_allowances"

    id = Column(Integer, primary_key=True, autoincrement=True)
    expense_allowance_fixed_id = Column(Integer, nullable=False)
    award_code = Column(String(50), nullable=False, index=True)
    clause_fixed_id = Column(Integer, nullable=True)
    clauses = Column(String(100), nullable=True)
    parent_allowance = Column(String(500), nullable=True)
    allowance = Column(String(500), nullable=True)
    is_all_purpose = Column(Boolean, default=False)
    allowance_amount = Column(Float, nullable=True)
    payment_frequency = Column(String(100), nullable=True)
    last_adjusted_year = Column(Integer, nullable=True)
    cpi_quarter_last_adjusted = Column(String(50), nullable=True)
    operative_from = Column(DateTime, nullable=True)
    operative_to = Column(DateTime, nullable=True)
    version_number = Column(Integer, nullable=True)
    last_modified_datetime = Column(DateTime, nullable=True)
    published_year = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class WageAllowance(Base):
    """Wage allowance model."""

    __tablename__ = "wage_allowances"

    id = Column(Integer, primary_key=True, autoincrement=True)
    wage_allowance_fixed_id = Column(Integer, nullable=False)
    award_code = Column(String(50), nullable=False, index=True)
    clause_fixed_id = Column(Integer, nullable=True)
    clauses = Column(String(100), nullable=True)
    parent_allowance = Column(String(500), nullable=True)
    allowance = Column(String(500), nullable=True)
    is_all_purpose = Column(Boolean, default=False)
    rate = Column(Float, nullable=True)
    rate_unit = Column(String(50), nullable=True)
    base_pay_rate_id = Column(String(50), nullable=True)
    allowance_amount = Column(Float, nullable=True)
    payment_frequency = Column(String(100), nullable=True)
    operative_from = Column(DateTime, nullable=True)
    operative_to = Column(DateTime, nullable=True)
    version_number = Column(Integer, nullable=True)
    last_modified_datetime = Column(DateTime, nullable=True)
    published_year = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class ETLJobLog(Base):
    """ETL job execution log."""

    __tablename__ = "etl_job_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(100), nullable=False, unique=True, index=True)
    pipeline_name = Column(String(200), nullable=False)
    status = Column(String(50), nullable=False)  # pending, running, success, failed
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    total_records = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    parameters = Column(Text, nullable=True)  # JSON
    created_at = Column(DateTime, default=datetime.now)


class ETLJobDetail(Base):
    """Detailed step-by-step log for ETL jobs."""

    __tablename__ = "etl_job_details"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(100), nullable=False, index=True)
    step_name = Column(String(200), nullable=False)
    step_type = Column(String(50), nullable=False)  # extract, transform, load
    status = Column(String(50), nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    records_processed = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    error_details = Column(Text, nullable=True)  # JSON
    created_at = Column(DateTime, default=datetime.now)


class RawAPIResponse(Base):
    """Raw API responses storage."""

    __tablename__ = "raw_api_responses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(100), nullable=False, index=True)
    endpoint_name = Column(String(200), nullable=False)
    response_json = Column(Text, nullable=False)  # NVARCHAR(MAX) in SQL Server
    record_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)
