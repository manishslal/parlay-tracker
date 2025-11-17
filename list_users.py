import os
from models import db, User
from flask import Flask

app = Flask(__name__)
database_url = os.environ.get('DATABASE_URL')
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
if database_url.startswith('postgresql://'):
    if '?' in database_url:
        database_url += '&sslmode=require'
    else:
        database_url += '?sslmode=require'
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
db.init_app(app)

with app.app_context():
    users = User.query.all()
    for user in users:
        print(f"Username: {user.username}, Email: {user.email}")
    if not users:
        print("No users found in the PostgreSQL database.")
