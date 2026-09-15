import sqlite3
p='instance/team.sqlite3'
conn=sqlite3.connect(p)
cur=conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables=cur.fetchall()
print('TABLES:', tables)
for t in tables:
    print('TABLE:',t)
if any('station' in t[0].lower() for t in tables):
    cur.execute('PRAGMA table_info(station)')
    print('STATION_SCHEMA:', cur.fetchall())
    cur.execute('SELECT * FROM station')
    rows = cur.fetchall()
    print('STATION_ROWS_COUNT:', len(rows))
    for r in rows:
        print(r)
conn.close()
