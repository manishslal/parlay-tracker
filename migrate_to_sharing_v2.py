#!/usr/bin/env python3
"""
Migration script: bet_users table → array columns in bets table
Run this ONCE to migrate from the many-to-many bet sharing system to the new array-based system

BEFORE running:
1. Back up your database
2. Test in development first
3. Review MIGRATION_BET_SHARING_V2.md

AFTER running:
1. Test all bet views work correctly
2. Verify users can still see shared bets
3. If successful, drop bet_users table
"""

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from app import app, db
from models import Bet, User
from sqlalchemy import text

def backup_bet_users():
    """Create a backup of bet_users table data"""
    print("Creating backup of bet_users table...")
    
    with app.app_context():
        try:
            # Use db.session which already has proper SSL configuration
            result = db.session.execute(text("""
                SELECT bet_id, user_id, is_primary_bettor, created_at
                FROM bet_users
                ORDER BY bet_id, is_primary_bettor DESC
            """))
            
            backup_data = result.fetchall()
            
            # Save to file
            with open('bet_users_backup.sql', 'w') as f:
                f.write("-- Backup of bet_users table\n")
                f.write(f"-- Created: {__import__('datetime').datetime.now()}\n\n")
                
                for bet_id, user_id, is_primary, created_at in backup_data:
                    created_str = created_at.strftime('%Y-%m-%d %H:%M:%S') if created_at else 'NOW()'
                    f.write(f"INSERT INTO bet_users (bet_id, user_id, is_primary_bettor, created_at) "
                           f"VALUES ({bet_id}, {user_id}, {is_primary}, '{created_str}');\n")
            
            print(f"✓ Backed up {len(backup_data)} records to bet_users_backup.sql\n")
            return True
            
        except Exception as e:
            print(f"✗ Backup failed: {e}\n")
            return False

def add_columns():
    """Add secondary_bettors and watchers columns"""
    print("Step 1: Adding new columns to bets table...")
    
    with app.app_context():
        try:
            db.session.execute(text("""
                ALTER TABLE bets 
                ADD COLUMN IF NOT EXISTS secondary_bettors INTEGER[] DEFAULT '{}',
                ADD COLUMN IF NOT EXISTS watchers INTEGER[] DEFAULT '{}';
            """))
            db.session.commit()
            
            # Add indexes for performance
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_bets_secondary_bettors 
                ON bets USING GIN(secondary_bettors);
                
                CREATE INDEX IF NOT EXISTS idx_bets_watchers 
                ON bets USING GIN(watchers);
            """))
            db.session.commit()
            
            print("✓ Columns added")
            print("✓ Indexes created\n")
            return True
            
        except Exception as e:
            print(f"✗ Error: {e}\n")
            db.session.rollback()
            return False

def migrate_data():
    """Migrate data from bet_users to array columns"""
    print("Step 2: Migrating data from bet_users table...")
    
    with app.app_context():
        try:
            # Get all unique bet IDs
            result = db.session.execute(text("""
                SELECT DISTINCT bet_id FROM bet_users ORDER BY bet_id
            """))
            bet_ids = [row[0] for row in result.fetchall()]
            
            print(f"Found {len(bet_ids)} bets to migrate")
            
            migrated = 0
            errors = 0
            
            for bet_id in bet_ids:
                try:
                    # Get primary bettor
                    primary_result = db.session.execute(text("""
                        SELECT user_id 
                        FROM bet_users 
                        WHERE bet_id = :bet_id AND is_primary_bettor = TRUE
                        LIMIT 1
                    """), {'bet_id': bet_id})
                    
                    primary = primary_result.fetchone()
                    
                    if not primary:
                        print(f"  ⚠️  Bet {bet_id} has no primary bettor, skipping...")
                        errors += 1
                        continue
                    
                    primary_user_id = primary[0]
                    
                    # Get secondary bettors (was viewers, now secondary)
                    secondary_result = db.session.execute(text("""
                        SELECT ARRAY_AGG(user_id) 
                        FROM bet_users 
                        WHERE bet_id = :bet_id AND is_primary_bettor = FALSE
                    """), {'bet_id': bet_id})
                    
                    secondary_row = secondary_result.fetchone()
                    secondary_ids = secondary_row[0] if secondary_row[0] else []
                    
                    # Update the bet
                    db.session.execute(text("""
                        UPDATE bets
                        SET 
                            user_id = :user_id,
                            secondary_bettors = :secondary_bettors,
                            watchers = '{}'
                        WHERE id = :bet_id
                    """), {
                        'bet_id': bet_id,
                        'user_id': primary_user_id,
                        'secondary_bettors': secondary_ids
                    })
                    
                    migrated += 1
                    
                    if migrated % 10 == 0:
                        db.session.commit()
                        print(f"  Migrated {migrated} bets...")
                
                except Exception as e:
                    print(f"  ✗ Error migrating bet {bet_id}: {e}")
                    errors += 1
            
            db.session.commit()
            
            print(f"\n✓ Migration complete:")
            print(f"  • {migrated} bets successfully migrated")
            print(f"  • {errors} errors\n")
            
            return errors == 0
            
        except Exception as e:
            print(f"✗ Migration failed: {e}\n")
            db.session.rollback()
            return False

def verify_migration():
    """Verify the migration was successful"""
    print("Step 3: Verifying migration...")
    
    with app.app_context():
        try:
            # Check for bets without primary bettor
            result = db.session.execute(text("""
                SELECT COUNT(*) FROM bets WHERE user_id IS NULL
            """))
            no_primary = result.scalar()
            
            # Count bets with secondary bettors
            result = db.session.execute(text("""
                SELECT COUNT(*) 
                FROM bets 
                WHERE array_length(secondary_bettors, 1) > 0
            """))
            with_secondary = result.scalar()
            
            # Compare counts with bet_users
            result = db.session.execute(text("""
                SELECT 
                    COUNT(DISTINCT bet_id) as total_bets,
                    COUNT(CASE WHEN is_primary_bettor THEN 1 END) as primary_count,
                    COUNT(CASE WHEN NOT is_primary_bettor THEN 1 END) as secondary_count
                FROM bet_users
            """))
            old_stats = result.fetchone()
            
            # Get sample of migrated bets
            result = db.session.execute(text("""
                SELECT 
                    b.id,
                    b.bet_id,
                    b.user_id,
                    u.username,
                    b.secondary_bettors,
                    array_length(b.secondary_bettors, 1) as num_secondary
                FROM bets b
                JOIN users u ON b.user_id = u.id
                WHERE array_length(b.secondary_bettors, 1) > 0
                LIMIT 5
            """))
            samples = result.fetchall()
            
            print("\nMigration Statistics:")
            print("-" * 70)
            print(f"Bets without primary bettor: {no_primary}")
            print(f"Bets with secondary bettors: {with_secondary}")
            print(f"\nOld system (bet_users):")
            print(f"  • Total bets: {old_stats[0]}")
            print(f"  • Primary bettors: {old_stats[1]}")
            print(f"  • Secondary/viewers: {old_stats[2]}")
            
            if samples:
                print("\nSample migrated bets:")
                print("-" * 70)
                for sample in samples:
                    print(f"  Bet {sample[0]} ({sample[1]}):")
                    print(f"    Primary: {sample[3]} (user_id={sample[2]})")
                    print(f"    Secondary: {sample[4]} ({sample[5]} users)")
            
            print("-" * 70)
            
            # Final verdict
            if no_primary > 0:
                print("\n⚠️  WARNING: Some bets have no primary bettor!")
                print("   Review these bets before proceeding.")
                return False
            else:
                print("\n✅ VERIFICATION PASSED")
                print("\nThe migration appears successful!")
                return True
                
        except Exception as e:
            print(f"✗ Verification failed: {e}\n")
            return False

def main():
    print("=" * 70)
    print("BET SHARING SYSTEM V2 MIGRATION")
    print("=" * 70)
    print()
    print("This will migrate from bet_users table to array columns.")
    print()
    
    response = input("Continue? (yes/no): ")
    if response.lower() != 'yes':
        print("Migration cancelled.")
        return
    
    print()
    
    # Step 0: Backup
    if not backup_bet_users():
        print("Backup failed. Aborting migration.")
        return
    
    # Step 1: Add columns
    if not add_columns():
        print("Failed to add columns. Aborting migration.")
        return
    
    # Step 2: Migrate data
    if not migrate_data():
        print("Data migration failed. Check errors above.")
        print("Your data is safe - bet_users table is unchanged.")
        return
    
    # Step 3: Verify
    if not verify_migration():
        print("\nVerification failed. Review the issues before proceeding.")
        print("Your data is safe - bet_users table is unchanged.")
        return
    
    print("\n" + "=" * 70)
    print("MIGRATION COMPLETE")
    print("=" * 70)
    print()
    print("Next steps:")
    print("1. Test the application thoroughly:")
    print("   - Check /live, /historical views")
    print("   - Verify users can see shared bets")
    print("   - Test bet creation with new methods")
    print()
    print("2. Update your code:")
    print("   - Remove bet_users table references")
    print("   - Update models.py (see MIGRATION_BET_SHARING_V2.md)")
    print("   - Update app.py query methods")
    print("   - Update bet creation scripts")
    print()
    print("3. After confirming everything works:")
    print("   DROP TABLE bet_users;")
    print()
    print("Backup saved to: bet_users_backup.sql")
    print()

if __name__ == '__main__':
    main()
