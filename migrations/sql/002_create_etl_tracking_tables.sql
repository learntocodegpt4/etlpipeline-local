-- Migration: 002_create_etl_tracking_tables.sql
-- Creates tables for ETL job tracking and logging

-- ETL Job Logs table
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='etl_job_logs' AND xtype='U')
CREATE TABLE etl_job_logs (
    id INT IDENTITY(1,1) PRIMARY KEY,
    job_id NVARCHAR(50) NOT NULL UNIQUE,
    status NVARCHAR(20) NOT NULL,
    start_time DATETIME2 NOT NULL,
    end_time DATETIME2 NULL,
    duration_seconds DECIMAL(18,2) NULL,
    total_records_processed INT DEFAULT 0,
    error_count INT DEFAULT 0,
    warning_count INT DEFAULT 0,
    error_message NVARCHAR(MAX) NULL,
    created_at DATETIME2 DEFAULT GETUTCDATE()
);
GO

CREATE INDEX IF NOT EXISTS ix_etl_job_logs_job_id ON etl_job_logs(job_id);
GO

CREATE INDEX IF NOT EXISTS ix_etl_job_logs_status ON etl_job_logs(status);
GO

CREATE INDEX IF NOT EXISTS ix_etl_job_logs_status_start ON etl_job_logs(status, start_time);
GO

-- ETL Job Details table
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='etl_job_details' AND xtype='U')
CREATE TABLE etl_job_details (
    id INT IDENTITY(1,1) PRIMARY KEY,
    job_id NVARCHAR(50) NOT NULL,
    step_name NVARCHAR(100) NOT NULL,
    status NVARCHAR(20) NOT NULL,
    start_time DATETIME2 NULL,
    end_time DATETIME2 NULL,
    duration_seconds DECIMAL(18,2) NULL,
    records_processed INT DEFAULT 0,
    records_failed INT DEFAULT 0,
    error_message NVARCHAR(MAX) NULL,
    details NVARCHAR(MAX) NULL,
    created_at DATETIME2 DEFAULT GETUTCDATE(),
    CONSTRAINT FK_job_details_job_id FOREIGN KEY (job_id) REFERENCES etl_job_logs(job_id)
);
GO

CREATE INDEX IF NOT EXISTS ix_etl_job_details_job_id ON etl_job_details(job_id);
GO

-- Raw API Responses table
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='raw_api_responses' AND xtype='U')
CREATE TABLE raw_api_responses (
    id INT IDENTITY(1,1) PRIMARY KEY,
    job_id NVARCHAR(50) NOT NULL,
    data_type NVARCHAR(50) NOT NULL,
    response_data NVARCHAR(MAX) NOT NULL,
    record_count INT NULL,
    extracted_at DATETIME2 NOT NULL,
    created_at DATETIME2 DEFAULT GETUTCDATE()
);
GO

CREATE INDEX IF NOT EXISTS ix_raw_api_responses_job_id ON raw_api_responses(job_id);
GO

CREATE INDEX IF NOT EXISTS ix_raw_api_responses_job_type ON raw_api_responses(job_id, data_type);
GO

PRINT 'ETL tracking tables created successfully';
GO
