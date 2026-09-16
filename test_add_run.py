"""
Simple integration test used during development to verify that the
`/add` route creates a `Run` and associated `Station` rows correctly.

This script uses Flask's `test_client()` inside an application
context so it can exercise the route without running the server.

What it demonstrates:
- Creating the DB schema with `db.create_all()` (safe for dev/test)
- Posting to the `/add` route with a simple form payload
- Querying the `Run` table to ensure the run was persisted

This is not a full unit test; it's a convenience script for local
development. For a real test-suite you would use a test framework such
as `pytest` and dedicated test fixtures.
"""

from app import app, db, Run
from datetime import date

with app.app_context():
    db.create_all()
    client = app.test_client()
    res = client.post('/add', data={'event_name':'Test Run','distance':'10','date':date.today().strftime('%Y-%m-%d')}, follow_redirects=True)
    print('POST status', res.status_code)
    runs = db.session.scalars(db.select(Run)).all()
    print('RUNS COUNT', len(runs))
    for r in runs:
        print(r.id, r.event_name, r.date, r.distance)
