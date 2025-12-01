import os
from dotenv import load_dotenv
load_dotenv()
url = os.environ.get("DATABASE_URL", "")
if "@" in url:
    print(f"DB Host: {url.split('@')[1].split(':')[0]}")
else:
    print("DB URL format not recognized or local")
