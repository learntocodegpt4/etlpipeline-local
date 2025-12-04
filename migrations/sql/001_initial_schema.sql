-- FWC ETL Pipeline Database Schema
-- Migration 001: Initial Schema

-- Awards table
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[awards]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[awards] (
        [id] INT IDENTITY(1,1) PRIMARY KEY,
        [award_id] INT NOT NULL,
        [award_fixed_id] INT NOT NULL,
        [code] NVARCHAR(50) NOT NULL,
        [name] NVARCHAR(500) NOT NULL,
        [award_operative_from] DATETIME NULL,
        [award_operative_to] DATETIME NULL,
        [version_number] INT NULL,
        [last_modified_datetime] DATETIME NULL,
        [published_year] INT NULL,
        [created_at] DATETIME DEFAULT GETDATE(),
        [updated_at] DATETIME DEFAULT GETDATE()
    );
    CREATE INDEX IX_awards_code ON [dbo].[awards] ([code]);
    CREATE INDEX IX_awards_fixed_year ON [dbo].[awards] ([award_fixed_id], [published_year]);
END
GO

-- Classifications table
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[classifications]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[classifications] (
        [id] INT IDENTITY(1,1) PRIMARY KEY,
        [classification_fixed_id] INT NOT NULL,
        [award_code] NVARCHAR(50) NOT NULL,
        [classification] NVARCHAR(500) NULL,
        [classification_level] INT NULL,
        [parent_classification_name] NVARCHAR(500) NULL,
        [employee_rate_type_code] NVARCHAR(50) NULL,
        [operative_from] DATETIME NULL,
        [operative_to] DATETIME NULL,
        [version_number] INT NULL,
        [published_year] INT NULL,
        [last_modified_datetime] DATETIME NULL,
        [created_at] DATETIME DEFAULT GETDATE(),
        [updated_at] DATETIME DEFAULT GETDATE()
    );
    CREATE INDEX IX_classifications_award_code ON [dbo].[classifications] ([award_code]);
    CREATE INDEX IX_classifications_composite ON [dbo].[classifications] ([award_code], [classification_fixed_id]);
END
GO

-- Pay rates table
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[pay_rates]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[pay_rates] (
        [id] INT IDENTITY(1,1) PRIMARY KEY,
        [classification_fixed_id] INT NOT NULL,
        [award_code] NVARCHAR(50) NOT NULL,
        [base_pay_rate_id] NVARCHAR(50) NULL,
        [base_rate_type] NVARCHAR(50) NULL,
        [base_rate] DECIMAL(18, 4) NULL,
        [calculated_pay_rate_id] NVARCHAR(50) NULL,
        [calculated_rate_type] NVARCHAR(50) NULL,
        [calculated_rate] DECIMAL(18, 4) NULL,
        [parent_classification_name] NVARCHAR(500) NULL,
        [classification] NVARCHAR(500) NULL,
        [classification_level] INT NULL,
        [employee_rate_type_code] NVARCHAR(50) NULL,
        [operative_from] DATETIME NULL,
        [operative_to] DATETIME NULL,
        [version_number] INT NULL,
        [published_year] INT NULL,
        [last_modified_datetime] DATETIME NULL,
        [created_at] DATETIME DEFAULT GETDATE(),
        [updated_at] DATETIME DEFAULT GETDATE()
    );
    CREATE INDEX IX_pay_rates_award_code ON [dbo].[pay_rates] ([award_code]);
    CREATE INDEX IX_pay_rates_composite ON [dbo].[pay_rates] ([award_code], [classification_fixed_id]);
END
GO

-- Expense allowances table
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[expense_allowances]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[expense_allowances] (
        [id] INT IDENTITY(1,1) PRIMARY KEY,
        [expense_allowance_fixed_id] INT NOT NULL,
        [award_code] NVARCHAR(50) NOT NULL,
        [clause_fixed_id] INT NULL,
        [clauses] NVARCHAR(100) NULL,
        [parent_allowance] NVARCHAR(500) NULL,
        [allowance] NVARCHAR(500) NULL,
        [is_all_purpose] BIT DEFAULT 0,
        [allowance_amount] DECIMAL(18, 4) NULL,
        [payment_frequency] NVARCHAR(100) NULL,
        [last_adjusted_year] INT NULL,
        [cpi_quarter_last_adjusted] NVARCHAR(50) NULL,
        [operative_from] DATETIME NULL,
        [operative_to] DATETIME NULL,
        [version_number] INT NULL,
        [last_modified_datetime] DATETIME NULL,
        [published_year] INT NULL,
        [created_at] DATETIME DEFAULT GETDATE(),
        [updated_at] DATETIME DEFAULT GETDATE()
    );
    CREATE INDEX IX_expense_allowances_award_code ON [dbo].[expense_allowances] ([award_code]);
END
GO

-- Wage allowances table
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[wage_allowances]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[wage_allowances] (
        [id] INT IDENTITY(1,1) PRIMARY KEY,
        [wage_allowance_fixed_id] INT NOT NULL,
        [award_code] NVARCHAR(50) NOT NULL,
        [clause_fixed_id] INT NULL,
        [clauses] NVARCHAR(100) NULL,
        [parent_allowance] NVARCHAR(500) NULL,
        [allowance] NVARCHAR(500) NULL,
        [is_all_purpose] BIT DEFAULT 0,
        [rate] DECIMAL(18, 4) NULL,
        [rate_unit] NVARCHAR(50) NULL,
        [base_pay_rate_id] NVARCHAR(50) NULL,
        [allowance_amount] DECIMAL(18, 4) NULL,
        [payment_frequency] NVARCHAR(100) NULL,
        [operative_from] DATETIME NULL,
        [operative_to] DATETIME NULL,
        [version_number] INT NULL,
        [last_modified_datetime] DATETIME NULL,
        [published_year] INT NULL,
        [created_at] DATETIME DEFAULT GETDATE(),
        [updated_at] DATETIME DEFAULT GETDATE()
    );
    CREATE INDEX IX_wage_allowances_award_code ON [dbo].[wage_allowances] ([award_code]);
END
GO

-- ETL Job logs table
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[etl_job_logs]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[etl_job_logs] (
        [id] INT IDENTITY(1,1) PRIMARY KEY,
        [job_id] NVARCHAR(100) NOT NULL UNIQUE,
        [pipeline_name] NVARCHAR(200) NOT NULL,
        [status] NVARCHAR(50) NOT NULL,
        [started_at] DATETIME NOT NULL,
        [completed_at] DATETIME NULL,
        [total_records] INT DEFAULT 0,
        [error_message] NVARCHAR(MAX) NULL,
        [parameters] NVARCHAR(MAX) NULL,
        [created_at] DATETIME DEFAULT GETDATE()
    );
    CREATE INDEX IX_etl_job_logs_job_id ON [dbo].[etl_job_logs] ([job_id]);
    CREATE INDEX IX_etl_job_logs_status ON [dbo].[etl_job_logs] ([status]);
END
GO

-- ETL Job details table
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[etl_job_details]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[etl_job_details] (
        [id] INT IDENTITY(1,1) PRIMARY KEY,
        [job_id] NVARCHAR(100) NOT NULL,
        [step_name] NVARCHAR(200) NOT NULL,
        [step_type] NVARCHAR(50) NOT NULL,
        [status] NVARCHAR(50) NOT NULL,
        [started_at] DATETIME NULL,
        [completed_at] DATETIME NULL,
        [records_processed] INT DEFAULT 0,
        [error_message] NVARCHAR(MAX) NULL,
        [error_details] NVARCHAR(MAX) NULL,
        [created_at] DATETIME DEFAULT GETDATE()
    );
    CREATE INDEX IX_etl_job_details_job_id ON [dbo].[etl_job_details] ([job_id]);
END
GO

-- Raw API responses table
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[raw_api_responses]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[raw_api_responses] (
        [id] INT IDENTITY(1,1) PRIMARY KEY,
        [job_id] NVARCHAR(100) NOT NULL,
        [endpoint_name] NVARCHAR(200) NOT NULL,
        [response_json] NVARCHAR(MAX) NOT NULL,
        [record_count] INT DEFAULT 0,
        [created_at] DATETIME DEFAULT GETDATE()
    );
    CREATE INDEX IX_raw_api_responses_job_id ON [dbo].[raw_api_responses] ([job_id]);
END
GO
