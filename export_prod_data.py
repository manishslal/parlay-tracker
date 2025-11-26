import json
from app import app
from models import db, User, Player, Team
from datetime import date, datetime, time
from decimal import Decimal

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (datetime, date, time)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError ("Type %s not serializable" % type(obj))

def export_table(model, filename):
    print(f"Exporting {model.__tablename__}...")
    try:
        items = model.query.all()
        data = []
        for item in items:
            item_dict = {}
            for column in item.__table__.columns:
                val = getattr(item, column.name)
                item_dict[column.name] = val
            data.append(item_dict)
        
        with open(f'data/{filename}', 'w') as f:
            json.dump(data, f, default=json_serial, indent=2)
        print(f"Exported {len(data)} records to data/{filename}")
    except Exception as e:
        print(f"Error exporting {model.__tablename__}: {e}")

def export_all():
    with app.app_context():
        export_table(User, 'prod_users.json')
        export_table(Player, 'prod_players.json')
        export_table(Team, 'prod_teams.json')

if __name__ == "__main__":
    export_all()
