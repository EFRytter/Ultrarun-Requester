import sqlite3
p='team.sqlite3'
conn=sqlite3.connect(p)
cur=conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables=cur.fetchall()
print('TABLES:', tables)
found = any('station' in t[0].lower() for t in tables)
if found:
    try:
        cur.execute('PRAGMA table_info(station)')
        print('STATION_SCHEMA:', cur.fetchall())
    except Exception as e:
        print('SCHEMA_ERROR', e)
    try:
        cur.execute('SELECT * FROM station')
        rows = cur.fetchall()
        print('STATION_ROWS_COUNT:', len(rows))
        for r in rows:
            print(r)
    except Exception as e:
        print('SELECT_ERROR', e)
else:
    print('NO station TABLE')
conn.close()
