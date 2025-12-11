"""
Simple migration runner that ensures the target database exists and executes
SQL migration files from `migrations/sql`. It splits scripts on `GO` batch
separators and runs each batch.

Usage:
  python migrations/run_migrations.py

The script prompts for server, authentication method and credentials.
"""

import getpass
import pathlib
import re
import sys

try:
    import pyodbc
except Exception:
    print("pyodbc is required. Install it in your venv: pip install pyodbc")
    raise


DEFAULT_SERVER = "tcp:202.131.115.228,1433"
TARGET_DB = "RosteredAIDBDev"
SQL_FILES = [
    "migrations/sql/001_create_base_tables.sql",
    "migrations/sql/002_create_etl_tracking_tables.sql",
    "migrations/sql/003_create_migration_history.sql",
]


def read_sql_file(path: str) -> list:
    text = pathlib.Path(path).read_text(encoding="utf-8")
    # Split on lines that contain only GO (case-insensitive)
    parts = re.split(r"^\s*GO\s*$", text, flags=re.IGNORECASE | re.MULTILINE)
    return [p.strip() for p in parts if p.strip()]


def create_database_if_missing(conn, db_name: str):
    cur = conn.cursor()
    cur.execute(f"IF DB_ID(N'{db_name}') IS NULL CREATE DATABASE [{db_name}];")


def run_migrations_on_db(conn, sql_files: list):
    cur = conn.cursor()
    for sqlfile in sql_files:
        sql_path = pathlib.Path(sqlfile)
        if not sql_path.exists():
            print(f"Skipping missing file: {sqlfile}")
            continue
        print(f"Running {sqlfile}")
        statements = read_sql_file(sqlfile)
        for stmt in statements:
            try:
                cur.execute(stmt)
            except Exception:
                print("Error executing statement (truncated):", stmt[:400])
                raise


def main():
    server = input(f"Server [{DEFAULT_SERVER}]: ").strip() or DEFAULT_SERVER
    auth = input("Authentication (1=SQL Server Authentication, 2=Windows Authentication) [1]: ").strip() or "1"

    # Build connection string for 'master' to create DB if needed
    if auth == "2":
        conn_str_master = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};"
            "Trusted_Connection=Yes;TrustServerCertificate=Yes;DATABASE=master"
        )
        db_credentials = None
    else:
        user = input("Username [sa]: ").strip() or "sa"
        pwd = getpass.getpass("Password: ")
        conn_str_master = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};"
            f"UID={user};PWD={pwd};TrustServerCertificate=Yes;DATABASE=master"
        )
        db_credentials = (user, pwd)

    print(f"Connecting to {server} to ensure database '{TARGET_DB}' exists (connecting to master)...")
    try:
        with pyodbc.connect(conn_str_master, autocommit=True) as conn:
            try:
                create_database_if_missing(conn, TARGET_DB)
                print(f"Database check/creation complete (target: {TARGET_DB}).")
            except Exception as e:
                print("Warning: unable to create database. You may not have sufficient permissions.")
                print("Error:", e)
                print("If the database does not exist, please create it in SSMS or run this script with a user that has CREATE DATABASE rights.")

        # Now connect to the target database and run migrations
        if auth == "2":
            conn_str_target = (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};"
                f"Trusted_Connection=Yes;TrustServerCertificate=Yes;DATABASE={TARGET_DB}"
            )
        else:
            user, pwd = db_credentials
            conn_str_target = (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};"
                f"UID={user};PWD={pwd};TrustServerCertificate=Yes;DATABASE={TARGET_DB}"
            )

        print(f"Connecting to database '{TARGET_DB}' to run migrations...")
        with pyodbc.connect(conn_str_target, autocommit=True) as conn:
            run_migrations_on_db(conn, SQL_FILES)
            print("All migrations executed successfully.")

    except Exception as exc:
        print("Migration failed:", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()