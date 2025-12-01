from app import app, db
from sqlalchemy import text

with app.app_context():
    try:
        result = db.session.execute(text("SELECT version_num FROM alembic_version"))
        version = result.scalar()
        print(f"Current Alembic Version: {version}")
    except Exception as e:
        print(f"Error checking version: {e}")
