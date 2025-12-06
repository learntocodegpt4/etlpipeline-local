import pyodbc, urllib.parse
server = 'tcp:202.131.115.228,1433'   # note pyodbc SERVER format
user = 'sa'
raw = 'Piyush@23D!gita1'         # your real raw password
enc = urllib.parse.quote_plus(raw)
for p in (raw, enc):
    print('Trying password (sample):', p[:10] + ('...' if len(p)>10 else ''))
    try:
        conn = pyodbc.connect(f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};UID={user};PWD={p};TrustServerCertificate=Yes", timeout=5)
        print('Connected OK with this password form')
        conn.close()
        break
    except Exception as e:
        print('Failed:', repr(e))