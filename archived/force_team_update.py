#!/usr/bin/env python3
"""
Force immediate update of all team data, bypassing the 6-hour check.
Use this for:
- Initial setup
- After major events (trades, playoff seeding changes)
- Manual refresh when data seems stale
"""

import psycopg2
import os
import sys
from datetime import datetime

def force_update():
    """Clear all last_stats_update timestamps to force fresh update."""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ ERROR: DATABASE_URL environment variable not set")
        return False
    
    try:
        conn = psycopg2.connect(database_url, sslmode='require')
        cur = conn.cursor()
        
        print("🔄 Forcing team data update...")
        print("=" * 80)
        
        # Clear timestamps to force update
        cur.execute("UPDATE teams SET last_stats_update = NULL")
        affected = cur.rowcount
        conn.commit()
        
        print(f"✅ Cleared update timestamps for {affected} teams")
        print()
        print("Now running update script...")
        print("=" * 80)
        print()
        
        cur.close()
        conn.close()
        
        # Now run the actual update script
        import subprocess
        result = subprocess.run(
            [sys.executable, 'update_team_records.py'],
            cwd=os.path.dirname(__file__) or '.'
        )
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("⚠️  WARNING: This will force update ALL teams")
    print("This bypasses the 6-hour check and makes ~62 API calls")
    print()
    
    # Ask for confirmation
    response = input("Continue? (yes/no): ").strip().lower()
    if response == 'yes':
        success = force_update()
        sys.exit(0 if success else 1)
    else:
        print("Cancelled.")
        sys.exit(0)
