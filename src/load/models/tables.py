"""SQLAlchemy ORM models for database tables"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Float,
    Boolean,
    Text,
    Index,
    ForeignKey,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Award(Base):
    """Awards table model"""

    __tablename__ = "Stg_TblAwards"

    id = Column(Integer, primary_key=True, autoincrement=True)
    award_id = Column(Integer, nullable=False)
    award_fixed_id = Column(Integer, nullable=False)
    code = Column(String(50), nullable=False, index=True)
    name = Column(String(500), nullable=True)
    award_operative_from = Column(DateTime, nullable=True)
    award_operative_to = Column(DateTime, nullable=True)
    version_number = Column(Integer, nullable=True)
    last_modified_datetime = Column(DateTime, nullable=True)
    published_year = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_stg_tblawards_code_year", "code", "published_year"),
    )


class Classification(Base):
    """Classifications table model"""

    __tablename__ = "Stg_TblClassifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    classification_fixed_id = Column(Integer, nullable=False)
    award_code = Column(String(50), nullable=False, index=True)
    clause_fixed_id = Column(Integer, nullable=True)
    clauses = Column(String(200), nullable=True)
    clause_description = Column(String(1000), nullable=True)
    parent_classification_name = Column(String(500), nullable=True)
    classification = Column(String(500), nullable=True)
    classification_level = Column(Integer, nullable=True)
    next_down_classification_fixed_id = Column(Integer, nullable=True)
    next_up_classification_fixed_id = Column(Integer, nullable=True)
    operative_from = Column(DateTime, nullable=True)
    operative_to = Column(DateTime, nullable=True)
    version_number = Column(Integer, nullable=True)
    last_modified_datetime = Column(DateTime, nullable=True)
    published_year = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_stg_tblclassifications_award_year", "award_code", "published_year"),
    )


class PayRate(Base):
    """Pay rates table model"""

    __tablename__ = "Stg_TblPayRates"

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
    employee_rate_type_code = Column(String(20), nullable=True)
    operative_from = Column(DateTime, nullable=True)
    operative_to = Column(DateTime, nullable=True)
    version_number = Column(Integer, nullable=True)
    last_modified_datetime = Column(DateTime, nullable=True)
    published_year = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_stg_tblpayrates_award_year", "award_code", "published_year"),
    )


class ExpenseAllowance(Base):
    """Expense allowances table model"""

    __tablename__ = "Stg_TblExpenseAllowances"

    id = Column(Integer, primary_key=True, autoincrement=True)
    expense_allowance_fixed_id = Column(Integer, nullable=False)
    award_code = Column(String(50), nullable=False, index=True)
    clause_fixed_id = Column(Integer, nullable=True)
    clauses = Column(String(200), nullable=True)
    parent_allowance = Column(String(500), nullable=True)
    allowance = Column(String(500), nullable=True)
    is_all_purpose = Column(Boolean, nullable=True)
    allowance_amount = Column(Float, nullable=True)
    payment_frequency = Column(String(50), nullable=True)
    last_adjusted_year = Column(Integer, nullable=True)
    cpi_quarter_last_adjusted = Column(String(50), nullable=True)
    operative_from = Column(DateTime, nullable=True)
    operative_to = Column(DateTime, nullable=True)
    version_number = Column(Integer, nullable=True)
    last_modified_datetime = Column(DateTime, nullable=True)
    published_year = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_stg_tblexpenseallowances_award_year", "award_code", "published_year"),
    )


class WageAllowance(Base):
    """Wage allowances table model"""

    __tablename__ = "Stg_TblWageAllowances"

    id = Column(Integer, primary_key=True, autoincrement=True)
    wage_allowance_fixed_id = Column(Integer, nullable=False)
    award_code = Column(String(50), nullable=False, index=True)
    clause_fixed_id = Column(Integer, nullable=True)
    clauses = Column(String(200), nullable=True)
    parent_allowance = Column(String(500), nullable=True)
    allowance = Column(String(500), nullable=True)
    is_all_purpose = Column(Boolean, nullable=True)
    rate = Column(Float, nullable=True)
    rate_unit = Column(String(50), nullable=True)
    base_pay_rate_id = Column(String(50), nullable=True)
    allowance_amount = Column(Float, nullable=True)
    payment_frequency = Column(String(50), nullable=True)
    operative_from = Column(DateTime, nullable=True)
    operative_to = Column(DateTime, nullable=True)
    version_number = Column(Integer, nullable=True)
    last_modified_datetime = Column(DateTime, nullable=True)
    published_year = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_stg_tblwageallowances_award_year", "award_code", "published_year"),
    )


class ETLJobLog(Base):
    """ETL job execution history"""

    __tablename__ = "Tbletl_job_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(50), nullable=False, unique=True, index=True)
    status = Column(String(20), nullable=False, index=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    total_records_processed = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    warning_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship to job details
    details = relationship("ETLJobDetail", back_populates="job", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_tbletl_job_logs_status_start", "status", "start_time"),
    )


class ETLJobDetail(Base):
    """Detailed step-by-step ETL job logs"""

    __tablename__ = "Tbletl_job_details"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(50), ForeignKey("Tbletl_job_logs.job_id"), nullable=False, index=True)
    step_name = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    records_processed = Column(Integer, default=0)
    records_failed = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    details = Column(Text, nullable=True)  # JSON string for additional details
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship to job
    job = relationship("ETLJobLog", back_populates="details")


class RawAPIResponse(Base):
    """Store raw JSON responses from API"""

    __tablename__ = "raw_api_responses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(50), nullable=False, index=True)
    data_type = Column(String(50), nullable=False, index=True)
    response_data = Column(Text, nullable=False)  # NVARCHAR(MAX) equivalent
    record_count = Column(Integer, nullable=True)
    extracted_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_raw_api_responses_job_type", "job_id", "data_type"),
    )
