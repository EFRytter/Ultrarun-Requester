"""
Small helper script to inspect the default `team.sqlite3` database.

This file is intended to be run from the project root during development.
It connects to `team.sqlite3` and prints the available tables. If a
`station` table exists it will print the schema and rows for quick
debugging. This is useful when you want to confirm that migrations or
table creation succeeded and to quickly inspect station data.

Sections:
- Connect to SQLite database file `team.sqlite3` in the project root.
- List tables and inspect `station` table schema and rows if present.

Note: This is a development utility and not used by the running web
application. It directly opens the SQLite file and prints results.
"""

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
