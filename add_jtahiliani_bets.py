"""
Add 2 bets for user JTahiliani (Nov 9, 2025)
- Bet 1: NFL 2-Leg Parlay ($100 -> $180.37)
- Bet 2: Same Game Parlay + with 4 legs ($100 -> $136.96)
"""

import psycopg2
import json
from urllib.parse import urlparse
from datetime import datetime
from decimal import Decimal

DATABASE_URL = 'postgresql://parlays_user:wgEpC1q34LIekYv6uelYqSThFdoy8xJT@dpg-d43b4iripnbc73bmuv5g-a.virginia-postgres.render.com/parlays'

def add_bets():
    url = urlparse(DATABASE_URL)
    conn = psycopg2.connect(
        dbname=url.path[1:],
        user=url.username,
        password=url.password,
        host=url.hostname,
        port=url.port
    )
    
    try:
        cursor = conn.cursor()
        
        # User ID for JTahiliani
        user_id = 3
        
        # Timestamp for placed_at
        placed_at = datetime(2025, 11, 9, 20, 0, 0)  # Nov 9, 2025 8:00 PM
        
        print("=" * 70)
        print("ADDING BETS FOR USER: JTahiliani (ID: 3)")
        print("=" * 70)
        
        # ========================================================================
        # BET 1: NFL 2-Leg Parlay - BUF -6.5 spread, DET -6.5 spread
        # ========================================================================
        print("\n📝 BET 1: NFL 2-Leg Parlay")
        print("-" * 70)
        
        # Prepare bet_data JSON
        bet1_data = {
            'bet_id': f'JT-Nov9-Parlay1',
            'type': 'PARLAY',
            'parlay_type': 'standard',
            'sport': 'NFL',
            'sportsbook': 'FanDuel',
            'wager': 100.00,
            'bonus_bets_used': 100.00,
            'potential_return': 180.37,
            'bet_date': '2025-11-09',
            'placed_at': placed_at.isoformat()
        }
        
        cursor.execute("""
            INSERT INTO bets (
                user_id, bet_id, bet_type, betting_site, status,
                wager, potential_winnings, total_legs, legs_pending,
                bet_date, created_at, bet_data,
                is_active, is_archived, api_fetched
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            ) RETURNING id
        """, (
            user_id,
            bet1_data['bet_id'],
            'PARLAY',
            'FanDuel',
            'pending',
            Decimal('100.00'),      # wager
            Decimal('180.37'),      # potential_winnings
            2,                       # total_legs
            2,                       # legs_pending
            '2025-11-09',           # bet_date
            placed_at,              # created_at
            json.dumps(bet1_data),  # bet_data
            True,                    # is_active
            False,                   # is_archived
            'No'                     # api_fetched
        ))
        
        bet1_id = cursor.fetchone()[0]
        print(f"✅ Created Bet ID: {bet1_id}")
        print(f"   Type: 2-Leg NFL Parlay")
        print(f"   Wager: $100.00 → Potential: $180.37")
        
        # Link bet to user
        cursor.execute("""
            INSERT INTO bet_users (bet_id, user_id, is_primary_bettor)
            VALUES (%s, %s, %s)
        """, (bet1_id, user_id, True))
        print(f"   Linked to user JTahiliani")
        
        # Leg 1: BUF Bills -6.5 spread vs MIA
        cursor.execute("""
            INSERT INTO bet_legs (
                bet_id, leg_order, bet_type, bet_line_type, sport, parlay_sport,
                player_name, player_team, home_team, away_team,
                game_id, game_date, game_time, is_home_game,
                target_value, stat_type, original_leg_odds, final_leg_odds,
                status, game_status
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """, (
            bet1_id, 1, 'spread', 'spread', 'NFL', 'NFL',
            'Buffalo Bills', 'Buffalo Bills', 'BUF', 'MIA',
            '401772771', datetime(2025, 11, 9).date(), '18:00:00', True,
            Decimal('-6.5'), 'spread', -142, -142,
            'pending', 'scheduled'
        ))
        print(f"   Leg 1: BUF Bills -6.5 spread vs MIA (-142)")
        
        # Leg 2: DET Lions -6.5 spread vs WSH
        cursor.execute("""
            INSERT INTO bet_legs (
                bet_id, leg_order, bet_type, bet_line_type, sport, parlay_sport,
                player_name, player_team, home_team, away_team,
                game_id, game_date, game_time, is_home_game,
                target_value, stat_type, original_leg_odds, final_leg_odds,
                status, game_status
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """, (
            bet1_id, 2, 'spread', 'spread', 'NFL', 'NFL',
            'Detroit Lions', 'Detroit Lions', 'DET', 'WSH',
            '401772878', datetime(2025, 11, 9).date(), '21:25:00', True,
            Decimal('-6.5'), 'spread', -155, -155,
            'pending', 'scheduled'
        ))
        print(f"   Leg 2: DET Lions -6.5 spread vs WSH (-155)")
        
        # ========================================================================
        # BET 2: Same Game Parlay + (4 legs: Gibbs prop, DET spread, BUF spread, OKC ML)
        # ========================================================================
        print("\n📝 BET 2: Same Game Parlay + (4 Legs)")
        print("-" * 70)
        
        # Prepare bet_data JSON
        bet2_data = {
            'bet_id': f'JT-Nov9-SGPPlus',
            'type': 'SAME_GAME_PARLAY_PLUS',
            'parlay_type': 'same_game_plus',
            'sport': 'MULTI',
            'sportsbook': 'FanDuel',
            'wager': 100.00,
            'bonus_bets_used': 100.00,
            'potential_return': 136.96,
            'bet_date': '2025-11-09',
            'placed_at': placed_at.isoformat()
        }
        
        cursor.execute("""
            INSERT INTO bets (
                user_id, bet_id, bet_type, betting_site, status,
                wager, potential_winnings, total_legs, legs_pending,
                bet_date, created_at, bet_data,
                is_active, is_archived, api_fetched
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            ) RETURNING id
        """, (
            user_id,
            bet2_data['bet_id'],
            'SAME_GAME_PARLAY_PLUS',
            'FanDuel',
            'pending',
            Decimal('100.00'),      # wager
            Decimal('136.96'),      # potential_winnings
            4,                       # total_legs
            4,                       # legs_pending
            '2025-11-09',           # bet_date
            placed_at,              # created_at
            json.dumps(bet2_data),  # bet_data
            True,                    # is_active
            False,                   # is_archived
            'No'                     # api_fetched
        ))
        
        bet2_id = cursor.fetchone()[0]
        print(f"✅ Created Bet ID: {bet2_id}")
        print(f"   Type: Same Game Parlay + (4 legs)")
        print(f"   Wager: $100.00 → Potential: $136.96")
        
        # Link bet to user
        cursor.execute("""
            INSERT INTO bet_users (bet_id, user_id, is_primary_bettor)
            VALUES (%s, %s, %s)
        """, (bet2_id, user_id, True))
        print(f"   Linked to user JTahiliani")
        
        # Leg 1: Jahmyr Gibbs 75+ Rush & Rec Yards (player prop)
        cursor.execute("""
            INSERT INTO bet_legs (
                bet_id, leg_order, bet_type, bet_line_type, sport, parlay_sport,
                player_id, player_name, player_team, player_position,
                home_team, away_team,
                game_id, game_date, game_time, is_home_game,
                target_value, stat_type, original_leg_odds, final_leg_odds,
                status, game_status
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s
            )
        """, (
            bet2_id, 1, 'rushing_receiving_yards', 'over', 'NFL', 'NFL',
            144, 'Jahmyr Gibbs', 'Detroit Lions', 'RB',
            'DET', 'WSH',
            '401772878', datetime(2025, 11, 9).date(), '21:25:00', True,
            Decimal('75.0'), 'yards', -175, -175,
            'pending', 'scheduled'
        ))
        print(f"   Leg 1: Jahmyr Gibbs 75+ Rush & Rec Yards (-175)")
        
        # Leg 2: DET Lions -2.5 spread vs WSH (same game as Gibbs)
        cursor.execute("""
            INSERT INTO bet_legs (
                bet_id, leg_order, bet_type, bet_line_type, sport, parlay_sport,
                player_name, player_team, home_team, away_team,
                game_id, game_date, game_time, is_home_game,
                target_value, stat_type, final_leg_odds,
                status, game_status
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """, (
            bet2_id, 2, 'spread', 'spread', 'NFL', 'NFL',
            'Detroit Lions', 'Detroit Lions', 'DET', 'WSH',
            '401772878', datetime(2025, 11, 9).date(), '21:25:00', True,
            Decimal('-2.5'), 'spread', None,  # odds not shown for this leg
            'pending', 'scheduled'
        ))
        print(f"   Leg 2: DET Lions -2.5 spread vs WSH")
        
        # Leg 3: BUF Bills -2.5 spread vs MIA
        cursor.execute("""
            INSERT INTO bet_legs (
                bet_id, leg_order, bet_type, bet_line_type, sport, parlay_sport,
                player_name, player_team, home_team, away_team,
                game_id, game_date, game_time, is_home_game,
                target_value, stat_type, original_leg_odds, final_leg_odds,
                status, game_status
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """, (
            bet2_id, 3, 'spread', 'spread', 'NFL', 'NFL',
            'Buffalo Bills', 'Buffalo Bills', 'BUF', 'MIA',
            '401772771', datetime(2025, 11, 9).date(), '18:00:00', True,
            Decimal('-2.5'), 'spread', -375, -375,
            'pending', 'scheduled'
        ))
        print(f"   Leg 3: BUF Bills -2.5 spread vs MIA (-375)")
        
        # Leg 4: OKC Thunder -525 Moneyline vs MEM (early payout - store in bet_data)
        cursor.execute("""
            INSERT INTO bet_legs (
                bet_id, leg_order, bet_type, bet_line_type, sport, parlay_sport,
                player_name, player_team, home_team, away_team,
                game_id, game_date, game_time, is_home_game,
                target_value, stat_type, original_leg_odds, final_leg_odds,
                status, game_status
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """, (
            bet2_id, 4, 'moneyline', 'moneyline', 'NBA', 'NBA',
            'Oklahoma City Thunder', 'Oklahoma City Thunder', 'OKC', 'MEM',
            '401810049', datetime(2025, 11, 9).date(), '23:00:00', True,
            Decimal('1.0'), 'moneyline', -525, -525,
            'pending', 'scheduled'
        ))
        print(f"   Leg 4: OKC Thunder -525 Moneyline vs MEM (Early Payout eligible)")
        
        # Commit the transaction
        conn.commit()
        
        print("\n" + "=" * 70)
        print("✅ SUCCESS! Both bets added to database")
        print("=" * 70)
        print(f"\nBet 1 ID: {bet1_id}")
        print(f"Bet 2 ID: {bet2_id}")
        print(f"\nUser: JTahiliani (ID: {user_id})")
        print(f"Total Wagered: $200.00")
        print(f"Total Potential Return: $317.33")
        
        # Verify the bets were created
        print("\n" + "=" * 70)
        print("VERIFICATION")
        print("=" * 70)
        
        cursor.execute("""
            SELECT b.id, b.bet_type, b.wager, b.potential_winnings, 
                   COUNT(bl.id) as num_legs, b.status
            FROM bets b
            LEFT JOIN bet_legs bl ON b.id = bl.bet_id
            WHERE b.id IN (%s, %s)
            GROUP BY b.id
            ORDER BY b.id
        """, (bet1_id, bet2_id))
        
        bets = cursor.fetchall()
        for bet in bets:
            print(f"\nBet ID {bet[0]}:")
            print(f"  Type: {bet[1]}")
            print(f"  Wager: ${bet[2]}")
            print(f"  Potential: ${bet[3]}")
            print(f"  Legs: {bet[4]}")
            print(f"  Status: {bet[5]}")
        
        cursor.close()
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ ERROR: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    add_bets()
