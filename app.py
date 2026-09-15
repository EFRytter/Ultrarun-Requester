from flask import Flask, flash, request, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.security import generate_password_hash, check_password_hash
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///team.sqlite3'
app.config['SECRET_KEY'] = 'a-long-random-private-value'
db = SQLAlchemy(app)

class Team(db.Model):
    _id =db.Column("id", db.Integer, primary_key=True)
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

        
        # search for a matching username
        existing_team = db.session.scalars (
            db.select(Team).where(Team.username == username)
        ).first()

        if existing_team is not None and check_password_hash(existing_team.password_hash,password):
            return redirect(url_for('home'))
        else: 
            flash('Incorrect username or password')
            return redirect(url_for('login'))

    return render_template('login.html')

# the main page
@app.route('/home', methods=['GET', 'POST'])
def home():
    return render_template('home.html')

# page to create a new account
@app.route('/register', methods=['GET', 'POST'])
def new_account():
    if request.method == 'GET':
        return render_template('register.html')
    if request.method == 'POST':
        username = request.form.get('uname')
        true_password = request.form.get('psw')
        confirmed_password = request.form.get('psw2')
        
        # check if the confirmed password is equal to the true password
        if true_password != confirmed_password:
            flash('Password not matching')
            return redirect(url_for('new_account'))
         
        # search for an existing username 
        existing_team = db.session.scalars (
            db.select(Team).where(Team.username == username)
        ).first()

        # if a maching team exists, 
        if existing_team is not None:
            flash('Username already in use')
            return redirect(url_for('new_account'))
        else:
            password_hash = generate_password_hash(true_password) # generate a password hash
            register_account = Team(
                username = username,
                password_hash = password_hash
            )
            db.session.add(register_account)
            db.session.commit()
            return redirect(url_for('login'))         
            
    return render_template('register.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    app.run(debug=True)