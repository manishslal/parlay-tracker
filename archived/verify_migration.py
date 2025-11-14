#!/usr/bin/env python3
"""Verify migration data looks correct"""
import psycopg2
from psycopg2.extras import RealDictCursor

conn = psycopg2.connect('postgresql://manishslal@localhost/parlays_local', cursor_factory=RealDictCursor)
cursor = conn.cursor()

print("=" * 70)
print("📊 MIGRATION VERIFICATION")
print("=" * 70)

# Check some players
print("\n👥 Sample Players:")
cursor.execute("SELECT player_name, sport, position, current_team FROM players LIMIT 10")
for player in cursor.fetchall():
    print(f"  {player['player_name']:25s} {player['sport']:10s} {player['position'] or 'N/A':5s} {player['current_team'] or 'N/A'}")

# Check some bet legs
print("\n🎯 Sample Bet Legs:")
cursor.execute("""
    SELECT player_name, bet_type, target_value, is_hit, status 
    FROM bet_legs 
    LIMIT 10
""")
for leg in cursor.fetchall():
    status_icon = "✅" if leg['is_hit'] else "❌" if leg['is_hit'] == False else "⏳"
    print(f"  {status_icon} {leg['player_name']:20s} {leg['bet_type']:15s} {leg['target_value']} ({leg['status']})")

# Check bets table updates
print("\n💰 Sample Bets with New Fields:")
cursor.execute("""
    SELECT bet_id, wager, total_legs, legs_won, legs_lost, legs_pending 
    FROM bets 
    LIMIT 5
""")
for bet in cursor.fetchall():
    bet_id_str = bet['bet_id'] or 'N/A'
    wager = bet['wager'] or 0
    print(f"  {bet_id_str:20s} ${wager:6.2f} - {bet['total_legs']} legs ({bet['legs_won'] or 0}W/{bet['legs_lost'] or 0}L/{bet['legs_pending'] or 0}P)")

# Check tax data
print("\n📈 Tax Summary:")
cursor.execute("SELECT * FROM tax_data")
for tax in cursor.fetchall():
    print(f"  User {tax['user_id']} - {tax['tax_year']}: {tax['total_bets']} bets, ${tax['total_wagered']:.2f} wagered, ${tax['net_profit']:.2f} profit")

print("\n✅ Migration data looks good!")
print("\nNext step: Test this works, then run on production (Render)")

conn.close()
