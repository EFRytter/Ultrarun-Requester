from flask import Flask, flash, request, render_template, redirect, url_for, session, abort
import os
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date

app = Flask(__name__)
# Ensure the instance folder exists and use an absolute path to avoid
# 'unable to open database file' errors when running from different CWDs.
os.makedirs(app.instance_path, exist_ok=True)
db_path = os.path.join(app.instance_path, 'team.sqlite3')
# SQLite URIs must use forward slashes
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path.replace('\\', '/')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'a-long-random-private-value'
db = SQLAlchemy(app)

class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(500), nullable=False)

    runs = db.relationship('Run', backref='team', lazy=True)

class Run(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_name = db.Column(db.String(300), nullable=False)
    date = db.Column(db.Date, nullable=False)
    distance = db.Column(db.Float, nullable=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=True)
    stations = db.relationship('Station', backref='run', lazy=True)

class Station(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    distance = db.Column(db.Float, nullable=False)
    station_number = db.Column(db.Integer, nullable=False)
    run_id = db.Column(db.Integer, db.ForeignKey('run.id'), nullable=False)
    
    @property
    def event_run_id(self):
        return self.run_id

# page to create a new account
@app.route('/register', methods=['GET', 'POST'])
def new_account():
    if request.method == 'GET':
        return render_template('register.html')

    username = request.form.get('uname')
    true_password = request.form.get('psw')
    confirmed_password = request.form.get('psw2')

    if true_password != confirmed_password:
        flash('Password not matching')
        return redirect(url_for('new_account'))

    existing_team = db.session.scalars(
        db.select(Team).where(Team.username == username)
    ).first()

    if existing_team is not None:
        flash('Username already in use')
        return redirect(url_for('new_account'))

    password_hash = generate_password_hash(true_password)
    register_account = Team(username=username, password_hash=password_hash)
    db.session.add(register_account)
    db.session.commit()
    flash('Account created')
    return redirect(url_for('login'))

# Login page
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    username = request.form.get('uname')
    password = request.form.get('psw')

    existing_team = db.session.scalars(
        db.select(Team).where(Team.username == username)
    ).first()

    if existing_team is not None and check_password_hash(existing_team.password_hash, password):
        session['team_id'] = existing_team.id
        return redirect(url_for('profile'))

    flash('Incorrect username or password')
    return redirect(url_for('login'))

# profile page: show upcoming events
@app.route('/profile', methods=['GET'])
def profile():
    today = date.today()
    upcoming = db.session.scalars(
        db.select(Run).where(Run.date >= today).order_by(Run.date)
    ).all()
    completed = db.session.scalars(
        db.select(Run).where(Run.date < today).order_by(Run.date.desc())
    ).all()

    return render_template('profile.html', upcoming=upcoming, completed=completed)

# add event
@app.route('/add', methods=['GET', 'POST'])
def add_event():
    if request.method == 'GET':
        return render_template('addevent.html')

    # POST
    team_id = session.get('team_id')
    event_name = request.form.get('event_name')
    distance = request.form.get('distance')
    date_str = request.form.get('date')

    if not date_str:
        flash('Please provide a date for the event')
        return redirect(url_for('add_event'))

    try:
        event_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        flash('Invalid date format. Use YYYY-MM-DD.')
        return redirect(url_for('add_event'))

    if not team_id:
        first_team = db.session.scalars(db.select(Team)).first()
        team_id = first_team.id if first_team is not None else None

    new_run = Run(event_name=event_name, date=event_date, distance=float(distance) if distance else None, team_id=team_id)
    db.session.add(new_run)
    db.session.commit()
    
    # Save stations submitted in the add-event form. The form uses
    # repeated fields named 'station_name' and 'station_distance'.
    station_names = request.form.getlist('station_name')
    station_distances = request.form.getlist('station_distance')
    
    for idx, name in enumerate(station_names, start=1):
        if not name:
            continue
        # get matching distance if provided
        dist_val = 0.0
        try:
            if idx-1 < len(station_distances):
                raw = station_distances[idx-1]
                dist_val = float(raw) if raw else 0.0
        except ValueError:
            dist_val = 0.0
        
        station = Station(name=name, distance=dist_val, station_number=idx, run_id=new_run.id)
        db.session.add(station)
    
    db.session.commit()
    flash(f'Event "{event_name}" added')
    return redirect(url_for('profile'))
    return redirect(url_for('profile'))


# Run detail / home page showing supplies lists for a run
@app.route('/home/<int:run_id>', methods=['GET'])
def home(run_id):
    run = db.session.get(Run, run_id)
    if run is None:
        abort(404)

    stations = db.session.scalars(
        db.select(Station).where(Station.run_id == run_id).order_by(Station.station_number)
    ).all()

    # Placeholder category lists. Later these should be read from the DB selections.
    food = []
    liquids = []
    hygiene = []

    return render_template('home.html', run=run, stations=stations, food=food, liquids=liquids, hygiene=hygiene)


# Add station to a run
@app.route('/run/<int:run_id>/station/add', methods=['GET', 'POST'])
def add_station(run_id):
    run = db.session.get(Run, run_id)
    if run is None:
        abort(404)

    if request.method == 'GET':
        return render_template('addstation.html', run=run)

    # POST
    name = request.form.get('name')
    distance = request.form.get('distance')
    station_number = request.form.get('station_number')

    if not name:
        flash('Please provide a station name')
        return redirect(url_for('add_station', run_id=run_id))

    try:
        dist_val = float(distance) if distance else 0.0
    except ValueError:
        flash('Invalid distance')
        return redirect(url_for('add_station', run_id=run_id))

    try:
        sn = int(station_number) if station_number else None
    except ValueError:
        flash('Invalid station number')
        return redirect(url_for('add_station', run_id=run_id))

    new_station = Station(name=name, distance=dist_val, station_number=sn if sn is not None else 0, run_id=run_id)
    db.session.add(new_station)
    db.session.commit()
    return redirect(url_for('home', run_id=run_id))


# Station detail page showing items saved for that station
@app.route('/home/<int:run_id>/station/<int:station_id>', methods=['GET'])
def station_detail(run_id, station_id):
    run = db.session.get(Run, run_id)
    if run is None:
        abort(404)
    station = db.session.get(Station, station_id)
    if station is None or station.run_id != run_id:
        abort(404)

    # Placeholder lists for items per station. Later, replace with real selections from DB.
    food = []
    liquids = []
    hygiene = []

    return render_template('station.html', run=run, station=station, food=food, liquids=liquids, hygiene=hygiene)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    app.run(debug=True)