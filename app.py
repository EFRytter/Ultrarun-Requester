"""
Main Flask application for the 100 Miles Food Requester.

High-level overview for new readers:
- Purpose: Provide a small web app that lets event teams create runs with stations
    and maintain per-station supply lists (food, liquids, other). Runners can
    select items per station and crew can view the lists.
- Structure: This file contains the Flask app setup, SQLAlchemy models,
    route handlers for the web UI, and JSON API endpoints used by the
    front-end JavaScript.
- Important sections:
    1. Configuration and database initialization (app, db)
    2. ORM models: `Team`, `Run`, `Station`, `Item`, `StationItem`
    3. Web routes: account/register/login/profile/add events and stations
    4. Run/station views: `home(run_id)` and `station_detail(run_id, station_id)`
    5. API endpoints: `/api/items` (GET/POST) and `/api/station_item` (POST)
"""

from flask import Flask, flash, request, render_template, redirect, url_for, session, abort
import os
import uuid
import vercel_blob
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, date

app = Flask(__name__)
database_url = os.environ.get('DATABASE_URL')

if database_url:
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
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


class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(300), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # 'food', 'liquids', 'other'
    carbs = db.Column(db.Float, nullable=True)
    calories = db.Column(db.Float, nullable=True)
    protein = db.Column(db.Float, nullable=True)
    image_filename = db.Column(db.String(300), nullable=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=True)

    def as_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'carbs': self.carbs,
            'calories': self.calories,
            'protein': self.protein,
            'image_filename': self.image_filename,
            'team_id': self.team_id,
        }


class StationItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    station_id = db.Column(db.Integer, db.ForeignKey('station.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    checked = db.Column(db.Boolean, nullable=False, default=False)

    station = db.relationship('Station', backref='station_items')
    item = db.relationship('Item', backref='station_items')

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

@app.route('/add', methods=['GET', 'POST'])
def add_event():
    if request.method == 'GET':
        return render_template('addevent.html')

    # POST handler: validate and create a new Run and its Stations
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

    new_run = Run(
        event_name=event_name,
        date=event_date,
        distance=float(distance) if distance else None,
        team_id=team_id,
    )
    db.session.add(new_run)
    db.session.commit()

    # Save any stations provided in the form (repeated fields)
    station_names = request.form.getlist('station_name')
    station_distances = request.form.getlist('station_distance')
    for idx, name in enumerate(station_names, start=1):
        if not name:
            continue
        dist_val = 0.0
        try:
            if idx - 1 < len(station_distances):
                raw = station_distances[idx - 1]
                dist_val = float(raw) if raw else 0.0
        except ValueError:
            dist_val = 0.0

        station = Station(name=name, distance=dist_val, station_number=idx, run_id=new_run.id)
        db.session.add(station)

    db.session.commit()
    flash(f'Event "{event_name}" added')
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

    # load items for the current user (team)
    team_id = session.get('team_id')
    if not team_id:
        first_team = db.session.scalars(db.select(Team)).first()
        team_id = first_team.id if first_team is not None else None

    items = db.session.scalars(db.select(Item).where(Item.team_id == team_id)).all() if team_id is not None else []
    food = [i for i in items if i.category == 'food']
    liquids = [i for i in items if i.category == 'liquids']
    other = [i for i in items if i.category == 'other']

    return render_template('home.html', run=run, stations=stations, food=food, liquids=liquids, other=other)


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

    team_id = session.get('team_id')
    if not team_id:
        first_team = db.session.scalars(db.select(Team)).first()
        team_id = first_team.id if first_team is not None else None

    items = db.session.scalars(db.select(Item).where(Item.team_id == team_id)).all() if team_id is not None else []
    food = [i for i in items if i.category == 'food']
    liquids = [i for i in items if i.category == 'liquids']
    other = [i for i in items if i.category == 'other']

    return render_template('station.html', run=run, station=station, food=food, liquids=liquids, other=other)


@app.route('/api/items', methods=['POST'])
def add_item():
    # accept multipart/form-data (for file) or JSON
    name = request.form.get('name') or (request.json and request.json.get('name'))
    category = request.form.get('category') or (request.json and request.json.get('category'))
    if not name or not category:
        return {'error': 'name and category required'}, 400

    try:
        carbs = float(request.form.get('carbs')) if request.form.get('carbs') else None
    except ValueError:
        carbs = None
    try:
        calories = float(request.form.get('calories')) if request.form.get('calories') else None
    except ValueError:
        calories = None
    try:
        protein = float(request.form.get('protein')) if request.form.get('protein') else None
    except ValueError:
        protein = None

    # determine team
    team_id = session.get('team_id')
    if not team_id:
        first_team = db.session.scalars(db.select(Team)).first()
        team_id = first_team.id if first_team is not None else None

    image_filename = None
    if 'image' in request.files:
        img = request.files['image']
        if img and img.filename:
            filename = secure_filename(img.filename)
            unique_name = f"{uuid.uuid4().hex}_{filename}"
            try:
                # Attempt to upload to Vercel Blob. The vercel_blob.put API may
                # return a dict or an object containing a URL; handle common shapes.
                resp = vercel_blob.put(unique_name, img.read())
                image_url = None
                if isinstance(resp, dict):
                    image_url = resp.get('url') or resp.get('public_url') or resp.get('publicUrl')
                else:
                    image_url = getattr(resp, 'url', None) or getattr(resp, 'public_url', None) or getattr(resp, 'publicUrl', None)
                # If response is a plain string URL
                if not image_url and isinstance(resp, str) and (resp.startswith('http://') or resp.startswith('https://')):
                    image_url = resp
                image_filename = image_url or unique_name
            except TypeError:
                # Some versions of the SDK may require an explicit token parameter.
                token = os.environ.get('BLOB_READ_WRITE_TOKEN')
                resp = vercel_blob.put(unique_name, img.read(), token)
                image_url = None
                if isinstance(resp, dict):
                    image_url = resp.get('url') or resp.get('public_url') or resp.get('publicUrl')
                else:
                    image_url = getattr(resp, 'url', None) or getattr(resp, 'public_url', None) or getattr(resp, 'publicUrl', None)
                if not image_url and isinstance(resp, str) and (resp.startswith('http://') or resp.startswith('https://')):
                    image_url = resp
                image_filename = image_url or unique_name
            except Exception:
                # If upload fails for any reason, leave image_filename as None
                image_filename = None

    item = Item(name=name, category=category, carbs=carbs, calories=calories, protein=protein, image_filename=image_filename, team_id=team_id)
    db.session.add(item)
    db.session.commit()

    # If run_id provided, create StationItem entries for all stations in that run
    run_id = request.form.get('run_id') or (request.json and request.json.get('run_id'))
    if run_id:
        try:
            rid = int(run_id)
            stations = db.session.scalars(db.select(Station).where(Station.run_id == rid)).all()
            for st in stations:
                si = StationItem(station_id=st.id, item_id=item.id, checked=False)
                db.session.add(si)
            db.session.commit()
        except Exception:
            db.session.rollback()

    resp = item.as_dict()
    if image_filename:
        # If we stored a full URL (from Vercel Blob), return it directly.
        if isinstance(image_filename, str) and (image_filename.startswith('http://') or image_filename.startswith('https://')):
            resp['image_url'] = image_filename
        else:
            # Fallback: legacy behavior for local filenames
            resp['image_url'] = url_for('static', filename=f'uploads/{image_filename}')

    return resp, 201


@app.route('/api/items/<int:item_id>/image', methods=['POST'])
def update_item_image(item_id):
    # Update image for an existing item (upload to Vercel Blob)
    item = db.session.get(Item, item_id)
    if item is None:
        return {'error': 'item not found'}, 404

    if 'image' not in request.files:
        return {'error': 'no image provided'}, 400

    img = request.files['image']
    if not img or not img.filename:
        return {'error': 'invalid image'}, 400

    filename = secure_filename(img.filename)
    unique_name = f"{uuid.uuid4().hex}_{filename}"
    try:
        resp = vercel_blob.put(unique_name, img.read())
        image_url = None
        if isinstance(resp, dict):
            image_url = resp.get('url') or resp.get('public_url') or resp.get('publicUrl')
        else:
            image_url = getattr(resp, 'url', None) or getattr(resp, 'public_url', None) or getattr(resp, 'publicUrl', None)
        if not image_url and isinstance(resp, str) and (resp.startswith('http://') or resp.startswith('https://')):
            image_url = resp
        item.image_filename = image_url or unique_name
        db.session.add(item)
        db.session.commit()
        out = item.as_dict()
        out['image_url'] = image_url or (url_for('static', filename=f'uploads/{item.image_filename}') if item.image_filename else None)
        return out, 200
    except TypeError:
        token = os.environ.get('BLOB_READ_WRITE_TOKEN')
        resp = vercel_blob.put(unique_name, img.read(), token)
        image_url = None
        if isinstance(resp, dict):
            image_url = resp.get('url') or resp.get('public_url') or resp.get('publicUrl')
        else:
            image_url = getattr(resp, 'url', None) or getattr(resp, 'public_url', None) or getattr(resp, 'publicUrl', None)
        if not image_url and isinstance(resp, str) and (resp.startswith('http://') or resp.startswith('https://')):
            image_url = resp
        item.image_filename = image_url or unique_name
        db.session.add(item)
        db.session.commit()
        out = item.as_dict()
        out['image_url'] = image_url or (url_for('static', filename=f'uploads/{item.image_filename}') if item.image_filename else None)
        return out, 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {'error': str(e)}, 500


@app.route('/api/items', methods=['GET'])
def list_items_for_station():
    station_id = request.args.get('station_id', type=int)
    team_id = session.get('team_id')
    if not team_id:
        first_team = db.session.scalars(db.select(Team)).first()
        team_id = first_team.id if first_team is not None else None

    items = db.session.scalars(db.select(Item).where(Item.team_id == team_id)).all() if team_id is not None else []
    result = []
    for it in items:
        checked = False
        if station_id:
            si = db.session.scalars(db.select(StationItem).where(StationItem.station_id == station_id, StationItem.item_id == it.id)).first()
            checked = bool(si.checked) if si is not None else False
        result.append({
            'id': it.id,
            'name': it.name,
            'category': it.category,
            'carbs': it.carbs,
            'calories': it.calories,
            'protein': it.protein,
            'image_filename': it.image_filename,
            'checked': checked,
        })

    return {'items': result}


@app.route('/api/station_item', methods=['POST'])
def set_station_item_checked():
    station_id = request.form.get('station_id') or (request.json and request.json.get('station_id'))
    item_id = request.form.get('item_id') or (request.json and request.json.get('item_id'))
    checked = request.form.get('checked') or (request.json and request.json.get('checked'))
    if station_id is None or item_id is None:
        return {'error': 'station_id and item_id required'}, 400
    try:
        sid = int(station_id)
        iid = int(item_id)
        checked_bool = True if str(checked).lower() in ('1','true','yes') else False
    except ValueError:
        return {'error': 'invalid ids'}, 400

    si = db.session.scalars(db.select(StationItem).where(StationItem.station_id == sid, StationItem.item_id == iid)).first()
    if si is None:
        si = StationItem(station_id=sid, item_id=iid, checked=checked_bool)
        db.session.add(si)
    else:
        si.checked = checked_bool
    db.session.commit()
    return {'ok': True}


if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    app.run(debug=False)