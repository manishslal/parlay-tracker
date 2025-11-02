#!/usr/bin/env python3
"""
Add Kyren Williams + Puka Nacua 3-Leg SGP for jtahiliani - PRODUCTION
======================================================================
This script adds the bet directly to the PostgreSQL database on Render.

Run this locally and it will connect to the production database.
"""

import os
import sys
import psycopg2
import json
from datetime import datetime

def add_bet_to_production():
    """Add the bet to production PostgreSQL database"""
    
    # Get DATABASE_URL from environment or prompt
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        print("\n❌ ERROR: DATABASE_URL environment variable not set!")
        print("\nPlease set it with your Render PostgreSQL connection string:")
        print("export DATABASE_URL='postgresql://...'")
        print("\nOr run this script on Render directly.")
        return
    
    # Fix Render's postgres:// to postgresql://
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    print("\n" + "="*60)
    print("ADD BET FOR JTAHILIANI - PRODUCTION DATABASE")
    print("="*60)
    print(f"\nConnecting to: {database_url[:50]}...")
    
    try:
        # Connect to database
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        # Find jtahiliani user
        cur.execute("SELECT id, username FROM users WHERE username = %s", ('jtahiliani',))
        user = cur.fetchone()
        
        if not user:
            print("\n❌ ERROR: User 'jtahiliani' not found!")
            print("Please create the user first or run migration script on Render.")
            cur.close()
            conn.close()
            return
        
        user_id, username = user
        print(f"\n✅ Found user: {username} (ID: {user_id})")
        
        # Bet data structure
        bet_data = {
            "name": "3 Pick Parlay",
            "type": "SGP",
            "odds": "+297",
            "wager": 20.0,
            "returns": 79.40,
            "betting_site": "FanDuel",
            "bet_id": None,
            "boost": "+50% Parlay Boost",
            "legs": [
                {
                    "game_date": "2025-11-02",
                    "away": "New Orleans Saints",
                    "home": "Los Angeles Rams",
                    "player": "Kyren Williams",
                    "target": 1,
                    "stat": "anytime_touchdown",
                    "stat_add": None,
                    "team": "Los Angeles Rams",
                    "position": "RB"
                },
                {
                    "game_date": "2025-11-02",
                    "away": "New Orleans Saints",
                    "home": "Los Angeles Rams",
                    "player": "Kyren Williams",
                    "target": 70,
                    "stat": "rushing_yards",
                    "stat_add": "over",
                    "team": "Los Angeles Rams",
                    "position": "RB"
                },
                {
                    "game_date": "2025-11-02",
                    "away": "New Orleans Saints",
                    "home": "Los Angeles Rams",
                    "player": "Puka Nacua",
                    "target": 90,
                    "stat": "receiving_yards",
                    "stat_add": "over",
                    "team": "Los Angeles Rams",
                    "position": "WR"
                }
            ],
            "bet_date": "2025-11-02",
            "sport": "NFL",
            "status": "live"
        }
        
        print("\n" + "="*60)
        print("BET DETAILS")
        print("="*60)
        print(f"Name: {bet_data['name']}")
        print(f"Type: {bet_data['type']}")
        print(f"Wager: ${bet_data['wager']}")
        print(f"To Pay: ${bet_data['returns']}")
        print(f"Odds: {bet_data['odds']}")
        print(f"Boost: {bet_data['boost']}")
        print(f"Site: {bet_data['betting_site']}")
        print(f"Status: {bet_data['status']}")
        print(f"\nLegs ({len(bet_data['legs'])}):")
        for i, leg in enumerate(bet_data['legs'], 1):
            print(f"  {i}. {leg['player']} - {leg['stat'].replace('_', ' ').title()} {leg['target']}")
            if leg['stat_add']:
                print(f"     ({leg['stat_add']})")
        
        # Insert bet into database
        insert_query = """
            INSERT INTO bets (
                user_id, bet_id, status, bet_type, betting_site, bet_date,
                created_at, updated_at, is_active, is_archived, api_fetched, bet_data
            ) VALUES (
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s
            ) RETURNING id
        """
        
        cur.execute(insert_query, (
            user_id,
            None,  # bet_id
            'live',  # status
            'SGP',  # bet_type
            'FanDuel',  # betting_site
            '2025-11-02',  # bet_date
            datetime.utcnow(),  # created_at
            datetime.utcnow(),  # updated_at
            True,  # is_active
            False,  # is_archived
            'No',  # api_fetched (will fetch live data)
            json.dumps(bet_data)  # bet_data
        ))
        
        bet_id = cur.fetchone()[0]
        
        # Also add to bet_users table (many-to-many relationship)
        cur.execute("""
            INSERT INTO bet_users (bet_id, user_id, is_primary_bettor, created_at)
            VALUES (%s, %s, %s, %s)
        """, (bet_id, user_id, True, datetime.utcnow()))
        
        conn.commit()
        
        print("\n" + "="*60)
        print("✅ SUCCESS!")
        print("="*60)
        print(f"Bet ID: {bet_id}")
        print(f"User: {username}")
        print(f"Status: live")
        print(f"Active: True")
        print(f"\nThe bet is now live in production and will fetch real-time stats from ESPN!")
        print(f"\nView it at your Render URL in the Live Bets tab")
        print(f"Or login as 'jtahiliani' to see it")
        
        cur.close()
        conn.close()
        
    except psycopg2.Error as e:
        print("\n" + "="*60)
        print("❌ DATABASE ERROR")
        print("="*60)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print("\n" + "="*60)
        print("❌ ERROR")
        print("="*60)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    add_bet_to_production()
