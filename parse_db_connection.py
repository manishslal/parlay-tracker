#!/usr/bin/env python3
"""
Parse PostgreSQL connection string for pgAdmin setup.
This extracts individual components from your DATABASE_URL.
"""

import os
import sys
from urllib.parse import urlparse

def parse_connection_string():
    """Parse DATABASE_URL and display components for pgAdmin."""
    
    # Get DATABASE_URL from environment
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        print("❌ ERROR: DATABASE_URL environment variable not set!")
        print("\nTo set it, run:")
        print("export DATABASE_URL='your_connection_string_from_render'")
        sys.exit(1)
    
    # Fix Render's postgres:// to postgresql://
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    # Parse the URL
    parsed = urlparse(database_url)
    
    print("\n" + "="*60)
    print("PostgreSQL Connection Details for pgAdmin")
    print("="*60)
    print("\nIn pgAdmin, create a new server with these settings:")
    print("\n📋 General Tab:")
    print(f"   Name: Parlay Tracker Production")
    
    print("\n📋 Connection Tab:")
    print(f"   Host name/address: {parsed.hostname}")
    print(f"   Port: {parsed.port or 5432}")
    print(f"   Maintenance database: {parsed.path[1:] if parsed.path else 'postgres'}")
    print(f"   Username: {parsed.username}")
    print(f"   Password: {parsed.password}")
    
    print("\n📋 SSL Tab:")
    print("   SSL mode: Require")
    
    print("\n💡 Note: Render requires SSL connections")
    print("="*60)
    
    # Also show the direct psql command
    print("\n🔧 Or connect via command line:")
    print(f'psql "{database_url}"')
    print("\n")

if __name__ == '__main__':
    parse_connection_string()
