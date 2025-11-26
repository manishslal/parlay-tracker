import json
import os
from app import app
from models import db, User, Player, Team
from datetime import datetime

def import_table(model, filename, unique_fields):
    filepath = f'data/{filename}'
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return

    print(f"Importing {model.__tablename__} from {filepath}...")
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return

    count = 0
    updated = 0
    
    for item_data in data:
        # Build filter for unique check
        filters = {k: item_data[k] for k in unique_fields}
        existing = model.query.filter_by(**filters).first()
        
        if existing:
            # Update fields
            for k, v in item_data.items():
                if hasattr(existing, k):
                    # Skip ID update
                    if k == 'id':
                        continue
                    setattr(existing, k, v)
            updated += 1
        else:
            # Create new
            new_item = model(**item_data)
            db.session.add(new_item)
            count += 1
            
    try:
        db.session.commit()
        print(f"Imported {count} new, updated {updated} existing records for {model.__tablename__}.")
    except Exception as e:
        db.session.rollback()
        print(f"Error importing {model.__tablename__}: {e}")

def import_all():
    with app.app_context():
        # Import Users first (dependencies)
        import_table(User, 'prod_users.json', ['id'])
        import_table(Team, 'prod_teams.json', ['id']) 
        import_table(Player, 'prod_players.json', ['id'])

if __name__ == "__main__":
    import_all()
