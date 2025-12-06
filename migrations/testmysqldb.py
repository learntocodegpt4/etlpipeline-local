import sqlite3, json, pathlib
db = pathlib.Path('../data/state.db')
print('state DB exists:', db.exists(), 'path=', db)
if not db.exists():
    raise SystemExit('state DB not found')
conn = sqlite3.connect(str(db))
cur = conn.cursor()
print('Jobs:')
for row in cur.execute('SELECT job_id, status, start_time, end_time, total_records_processed, error_message FROM jobs ORDER BY start_time DESC LIMIT 20'):
    print(row)
print('\\nJob steps (last 20):')
for row in cur.execute('SELECT job_id, step_name, status, records_processed, error_message FROM job_steps ORDER BY id DESC LIMIT 20'):
    print(row)
conn.close()