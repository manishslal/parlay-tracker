from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Bet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    # Add more fields and methods as needed
