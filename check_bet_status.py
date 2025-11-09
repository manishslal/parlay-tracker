#!/usr/bin/env python3
"""
Check the status of the 3 newest bets to debug duplicate issue
"""
import os
from sqlalchemy import create_engine, text

# Get database URL from environment
database_url = os.environ.get('DATABASE_URL')
if not database_url:
    print("ERROR: DATABASE_URL not set")
    exit(1)

# Fix for Render PostgreSQL
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

engine = create_engine(database_url)

with engine.connect() as conn:
    # Get the 3 newest bets
    result = conn.execute(text("""
        SELECT 
            b.id,
            b.bet_type,
            b.status,
            b.is_active,
            b.amount,
            b.potential_payout,
            COUNT(bu.user_id) as num_users
        FROM bets b
        LEFT JOIN bet_users bu ON b.id = bu.bet_id
        GROUP BY b.id
        ORDER BY b.id DESC
        LIMIT 5
    """))
    
    print("\n=== 5 Newest Bets ===")
    for row in result:
        print(f"\nBet ID: {row.id}")
        print(f"  Type: {row.bet_type}")
        print(f"  Status: {row.status}")
        print(f"  Is Active: {row.is_active}")
        print(f"  Amount: ${row.amount}")
        print(f"  Payout: ${row.potential_payout}")
        print(f"  Shared with {row.num_users} users")
    
    # Check for any duplicate bet_users entries
    result = conn.execute(text("""
        SELECT bet_id, user_id, COUNT(*) as count
        FROM bet_users
        GROUP BY bet_id, user_id
        HAVING COUNT(*) > 1
    """))
    
    duplicates = list(result)
    if duplicates:
        print("\n=== DUPLICATE bet_users entries found! ===")
        for row in duplicates:
            print(f"Bet {row.bet_id} + User {row.user_id}: {row.count} entries")
    else:
        print("\n✓ No duplicate bet_users entries")
    
    # Check the user_ids for the newest 3 bets
    result = conn.execute(text("""
        SELECT b.id, bu.user_id, bu.is_primary_bettor, u.username
        FROM bets b
        JOIN bet_users bu ON b.id = bu.bet_id
        JOIN users u ON bu.user_id = u.id
        WHERE b.id IN (
            SELECT id FROM bets ORDER BY id DESC LIMIT 3
        )
        ORDER BY b.id DESC, bu.user_id
    """))
    
    print("\n=== User Access for 3 Newest Bets ===")
    current_bet = None
    for row in result:
        if current_bet != row.id:
            print(f"\nBet {row.id}:")
            current_bet = row.id
        print(f"  - User {row.user_id} ({row.username}): {'PRIMARY' if row.is_primary_bettor else 'viewer'}")

print("\n✓ Done!")
