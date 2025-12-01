from app import app, db
from models import db as models_db
import sys

print(f"app.db id: {id(db)}")
print(f"models.db id: {id(models_db)}")
print(f"app id: {id(app)}")

try:
    with app.app_context():
        print(f"App extensions: {app.extensions.keys()}")
        if 'sqlalchemy' in app.extensions:
            print(f"SQLAlchemy state: {app.extensions['sqlalchemy']}")
            
        print(f"DB Engine: {db.engine}")
except Exception as e:
    print(f"Error: {e}")
