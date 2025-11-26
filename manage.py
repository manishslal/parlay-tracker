from app import app, db
from flask_migrate import Migrate

# Re-initialize to be sure, though it should be in app.py
migrate = Migrate(app, db)

if __name__ == '__main__':
    from flask.cli import FlaskGroup
    cli = FlaskGroup(create_app=lambda: app)
    cli()
