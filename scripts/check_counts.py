"""Check row counts in target MSSQL tables using the same connector settings the app uses.

Usage:
    python scripts\check_counts.py

This script will attempt to connect using the SQLAlchemy/ODBC connection built by `src.config.settings.get_settings()`
and print counts for the main ETL tables and `raw_api_responses`.
"""
import sys
import urllib.parse

from src.config.settings import get_settings
import pyodbc


def get_odbc_conn_from_settings():
    s = get_settings()
    url = s.database_url
    if 'odbc_connect=' in url:
        enc = url.split('odbc_connect=')[1]
        odbc_conn = urllib.parse.unquote_plus(enc)
        return odbc_conn
    # Fallback: try to build from MSSQL_* environment variables handled by settings
    raise RuntimeError('No odbc_connect in computed database_url')


def main():
    try:
        connstr = get_odbc_conn_from_settings()
        print('Using ODBC conn (masked):', connstr[:120] + '...')
        conn = pyodbc.connect(connstr, timeout=10)
    except Exception as e:
        print('Failed to connect via ODBC:', e)
        sys.exit(1)

    curs = conn.cursor()
    tables = [
        'Stg_TblAwards',
        'Stg_TblClassifications',
        'Stg_TblPayRates',
        'Stg_TblExpenseAllowances',
        'Stg_TblWageAllowances',
        'raw_api_responses',
    ]
    for t in tables:
        try:
            curs.execute(f"SELECT COUNT(*) FROM {t}")
            n = curs.fetchone()[0]
            print(f"{t}: {n}")
        except Exception as e:
            print(f"{t}: error - {e}")

    conn.close()


if __name__ == '__main__':
    main()
