#!/usr/bin/env python3
"""
Check Database Configuration - PRODUCTION
==========================================
This script checks:
1. What database you're connected to
2. What tables exist
3. How many users exist
4. If data is persisting
"""

import os
import psycopg2

def check_database():
    """Check database configuration"""
    
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        print("\n❌ ERROR: DATABASE_URL not set!")
        print("This means you're probably using SQLite (which gets wiped on deployment)")
        return
    
    # Fix Render's postgres:// to postgresql://
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    print("\n" + "="*70)
    print("DATABASE CONFIGURATION CHECK")
    print("="*70)
    
    # Mask the password in the URL for display
    display_url = database_url
    if '@' in display_url:
        parts = display_url.split('@')
        if ':' in parts[0]:
            user_pass = parts[0].split(':')
            display_url = f"{user_pass[0]}:****@{parts[1]}"
    
    print(f"\nDatabase URL: {display_url}")
    
    try:
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        print("\n✅ Successfully connected to PostgreSQL!")
        
        # Get database name
        cur.execute("SELECT current_database();")
        db_name = cur.fetchone()[0]
        print(f"✅ Connected to database: {db_name}")
        
        # List all tables
        cur.execute("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public'
            ORDER BY tablename;
        """)
        tables = cur.fetchall()
        
        print(f"\n📊 Tables in database ({len(tables)}):")
        for table in tables:
            print(f"   • {table[0]}")
        
        # Check users table
        if any(t[0] == 'users' for t in tables):
            cur.execute("SELECT COUNT(*) FROM users;")
            user_count = cur.fetchone()[0]
            print(f"\n👥 Users in database: {user_count}")
            
            if user_count > 0:
                cur.execute("SELECT id, username, email, created_at FROM users ORDER BY id;")
                users = cur.fetchall()
                print("\n   Users:")
                for user in users:
                    print(f"     • ID {user[0]}: {user[1]} ({user[2]}) - Created: {user[3]}")
        
        # Check bets table
        if any(t[0] == 'bets' for t in tables):
            cur.execute("SELECT COUNT(*) FROM bets;")
            bet_count = cur.fetchone()[0]
            print(f"\n🎲 Bets in database: {bet_count}")
            
            if bet_count > 0:
                cur.execute("""
                    SELECT id, user_id, status, bet_type, created_at 
                    FROM bets 
                    ORDER BY created_at DESC 
                    LIMIT 5;
                """)
                bets = cur.fetchall()
                print("\n   Recent bets:")
                for bet in bets:
                    print(f"     • Bet #{bet[0]}: User {bet[1]}, {bet[2]}, {bet[3]} - {bet[4]}")
        
        # Check bet_users table
        if any(t[0] == 'bet_users' for t in tables):
            cur.execute("SELECT COUNT(*) FROM bet_users;")
            bet_user_count = cur.fetchone()[0]
            print(f"\n🔗 Bet sharing relationships: {bet_user_count}")
        
        print("\n" + "="*70)
        print("DIAGNOSIS")
        print("="*70)
        
        if user_count == 0:
            print("\n⚠️  DATABASE IS EMPTY!")
            print("   Possible causes:")
            print("   1. This is a new/temporary database")
            print("   2. Database gets reset on each deployment")
            print("   3. Wrong DATABASE_URL configured")
            print("\n   Solution: Make sure you have a PERSISTENT PostgreSQL")
            print("   database service on Render, not an ephemeral one.")
        else:
            print("\n✅ DATABASE HAS DATA!")
            print("   Your PostgreSQL database is working correctly.")
            print("   Data should persist between deployments.")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_database()
