import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

db_url = os.environ.get("DATABASE_URL")

if not db_url:
    print("DATABASE_URL not found in .env")
else:
    try:
        conn = psycopg2.connect(db_url)
        print("Successfully connected to the database!")
        conn.close()
    except Exception as e:
        print(f"Failed to connect: {e}")
