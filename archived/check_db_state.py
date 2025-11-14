#!/usr/bin/env python3
"""Quick check of database state"""
import psycopg2

conn = psycopg2.connect('postgresql://manishslal@localhost/parlays_local')
cursor = conn.cursor()

# Check what tables exist
cursor.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    ORDER BY table_name
""")

tables = [row[0] for row in cursor.fetchall()]
print("Tables:", tables)

# Check if new columns exist on bets
cursor.execute("""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_name = 'bets' 
    ORDER BY ordinal_position
""")
columns = [row[0] for row in cursor.fetchall()]
print("\nBets columns:", columns)

# Check row counts
for table in tables:
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    count = cursor.fetchone()[0]
    print(f"{table}: {count} rows")

conn.close()
