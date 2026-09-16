import os
import sys

if len(sys.argv) < 2:
    print("Usage: python create_tables.py <DATABASE_URL>")
    sys.exit(1)

os.environ['DATABASE_URL'] = sys.argv[1]

from app import app, db

with app.app_context():
    db.create_all()
    print("Tables created successfully on the target database.")
