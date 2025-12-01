from app import app
import models
import sys
import os
import sqlalchemy

print(f"DEBUG: models file: {models.__file__}")
print(f"DEBUG: CWD: {os.getcwd()}")
# print(f"DEBUG: sys.path: {sys.path}") # Too verbose, maybe just check first few

with app.app_context():
    from models import Bet, db
    print(f"SQLAlchemy version: {sqlalchemy.__version__}")
    try:
        print(f"Bet.secondary_bettors type: {Bet.secondary_bettors.type}")
        print(f"Bet.watchers type: {Bet.watchers.type}")
    except AttributeError:
        print("Attributes secondary_bettors/watchers not found on Bet model")
        # Check for the test columns
        if hasattr(Bet, 'secondary_bettors_test'):
             print(f"Bet.secondary_bettors_test type: {Bet.secondary_bettors_test.type}")
        else:
             print("Bet.secondary_bettors_test not found")

    print(f"db.JSON: {db.JSON}")
