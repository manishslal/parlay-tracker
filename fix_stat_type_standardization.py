#!/usr/bin/env python3
"""
Fix all non-standardized alt stat types in the database.
This script will update all legs with alt_rushing_yds, alt_passing_yds, anytime_td_scorer, 
and any_time_touchdown_scorer to their canonical forms.
"""

from app import app, db
from stat_standardization import standardize_stat_type

with app.app_context():
    print("=" * 80)
    print("FIXING NON-STANDARDIZED STAT TYPES")
    print("=" * 80)
    
    # Find all the non-standardized stat types
    result = db.session.execute(db.text('''
        SELECT DISTINCT stat_type FROM bet_legs 
        WHERE stat_type IN (
            'alt_passing_yds', 
            'alt_rushing_yds', 
            'anytime_td_scorer',
            'any_time_touchdown_scorer'
        )
        ORDER BY stat_type
    '''))
    
    non_standard_types = [row[0] for row in result]
    print(f"\nFound {len(non_standard_types)} non-standardized stat types:")
    for stat_type in non_standard_types:
        print(f"  - {stat_type}")
    
    # For each non-standardized type, standardize it and update the database
    total_updated = 0
    for stat_type in non_standard_types:
        # Standardize it
        standardized = standardize_stat_type(stat_type, sport='NFL')
        
        # Count how many legs have this stat type
        count_result = db.session.execute(db.text('''
            SELECT COUNT(*) as cnt FROM bet_legs WHERE stat_type = :stat_type
        '''), {'stat_type': stat_type})
        
        count = count_result.scalar()
        
        print(f"\n{stat_type} → {standardized} ({count} legs)")
        
        if count > 0:
            # Update all legs with this stat type
            db.session.execute(db.text('''
                UPDATE bet_legs SET stat_type = :standardized WHERE stat_type = :original
            '''), {'standardized': standardized, 'original': stat_type})
            
            total_updated += count
            print(f"  ✓ Updated {count} legs")
    
    # Commit all changes
    db.session.commit()
    
    print("\n" + "=" * 80)
    print(f"✅ Successfully standardized {total_updated} legs")
    print("=" * 80)
    
    # Verify the fixes
    print("\nVerifying fixes...")
    result = db.session.execute(db.text('''
        SELECT DISTINCT stat_type FROM bet_legs 
        WHERE stat_type IN (
            'alt_passing_yds', 
            'alt_rushing_yds', 
            'anytime_td_scorer',
            'any_time_touchdown_scorer'
        )
    '''))
    
    remaining = result.fetchall()
    if not remaining:
        print("✓ All non-standardized stat types have been fixed!")
    else:
        print(f"❌ {len(remaining)} non-standardized types still remain:")
        for row in remaining:
            print(f"  - {row[0]}")
