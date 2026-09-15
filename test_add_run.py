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
