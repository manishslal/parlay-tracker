import os
from dotenv import load_dotenv

load_dotenv()
db_url = os.environ.get("DATABASE_URL")
print(f"DATABASE_URL: {db_url}")
if "sqlite" in db_url:
    print("SUCCESS: Using SQLite")
else:
    print("WARNING: Not using SQLite")
