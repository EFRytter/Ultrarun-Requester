from flask import Flask, flash, request, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.security import generate_password_hash, check_password_hash
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///team.sqlite3'

db = SQLAlchemy(app)

class Team(db.Model):
    _id =db.Column("id", db.Integer, primary_key=True)
    team_name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(500), nullable=False)

# Login page
@app.route('/', methods=['GET', 'POST'])
def login():
    username = None
    password = None
    if request.method == 'GET':
        return render_template('login.html')
    if request.method == 'POST':
        username = request.form.get('uname')
        password = request.form.get('psw')
        return redirect(url_for('home'))
#        check_password_hash(pwhash=password_hash, password=true_password)

    return render_template('login.html')

@app.route('/home', methods=['GET', 'POST'])
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def new_account():
    if request.method == 'GET':
        return render_template('register.html')
    if request.method == 'POST':
        team_name = request.form.get('teamname')
        username = request.form.get('uname')
        true_password = request.form.get('psw')
        confirmed_password = request.form.get('psw2')
        
        if true_password != confirmed_password:
            return redirect(url_for('register.html')) 
        
        password_hash = generate_password_hash(true_password,salt_length=8) # generate a password hash

        existing_team = db.session.scalars (
            db.select(Team).where(Team.username == username)
        ).first()

        if existing_team is not None:
            flash('Username already in use. Try again')
        else:
            
            

    return render_template('register.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    app.run(debug=True)