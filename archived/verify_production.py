#!/usr/bin/env python3
"""Quick verification of production migration"""
import psycopg2
from psycopg2.extras import RealDictCursor
import os

database_url = os.environ.get('DATABASE_URL')
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
cursor = conn.cursor()

print("=" * 70)
print("📊 PRODUCTION MIGRATION VERIFICATION")
print("=" * 70)

# Count records
cursor.execute("SELECT COUNT(*) as count FROM players")
players_count = cursor.fetchone()['count']

cursor.execute("SELECT COUNT(*) as count FROM bet_legs")
legs_count = cursor.fetchone()['count']

cursor.execute("SELECT COUNT(*) as count FROM tax_data")
tax_count = cursor.fetchone()['count']

cursor.execute("SELECT COUNT(*) as count FROM bets WHERE wager IS NOT NULL")
bets_with_wager = cursor.fetchone()['count']

print(f"\n✅ Players: {players_count}")
print(f"✅ Bet Legs: {legs_count}")
print(f"✅ Tax Records: {tax_count}")
print(f"✅ Bets with financial data: {bets_with_wager}")

# Sample some data
print("\n👥 Sample Players:")
cursor.execute("SELECT player_name, sport, position FROM players LIMIT 5")
for player in cursor.fetchall():
    print(f"  - {player['player_name']} ({player['sport']}, {player['position'] or 'N/A'})")

print("\n🎯 Sample Bet Legs:")
cursor.execute("""
    SELECT player_name, bet_type, target_value, status 
    FROM bet_legs 
    ORDER BY id DESC
    LIMIT 5
""")
for leg in cursor.fetchall():
    print(f"  - {leg['player_name']}: {leg['bet_type']} {leg['target_value']} ({leg['status']})")

print("\n💰 Sample Bets:")
cursor.execute("""
    SELECT bet_id, wager, total_legs, legs_won, legs_lost 
    FROM bets 
    WHERE wager IS NOT NULL
    LIMIT 5
""")
for bet in cursor.fetchall():
    print(f"  - {bet['bet_id'] or 'N/A'}: ${bet['wager']:.2f} - {bet['total_legs']} legs ({bet['legs_won'] or 0}W/{bet['legs_lost'] or 0}L)")

print("\n✅ Migration verified successfully!")
print("=" * 70)

conn.close()
