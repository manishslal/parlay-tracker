import os
import sys
import subprocess
from app import app
from debug_scoreboard import debug_scoreboard

def run_startup():
    print("="*50)
    print("STARTING PRODUCTION STARTUP TASKS")
    print("="*50)

    # 1. Run Migrations
    print("\n[1/2] Running Database Migrations...")
    try:
        # Run flask db upgrade
        subprocess.run([sys.executable, '-m', 'flask', 'db', 'upgrade'], check=True)
        print("Migrations completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Migration failed with exit code {e.returncode}")
        # We might want to exit here if migrations fail, but for now let's continue
        # sys.exit(1)
    except Exception as e:
        print(f"Migration failed: {e}")

    # 2. Force Create Audit Tables (Fallback)
    print("\n[2/3] Verifying Audit Tables...")
    try:
        from app import db
        from sqlalchemy import text
        with app.app_context():
            # Check if table exists
            result = db.session.execute(text("SELECT to_regclass('public.audit_log')")).scalar()
            if not result:
                print("Table 'audit_log' missing. Creating manually...")
                # SQL from migration file
                sql = """
                CREATE TABLE IF NOT EXISTS audit_log (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW() NOT NULL,
                    event_type VARCHAR(50) NOT NULL,
                    action VARCHAR(100) NOT NULL,
                    actor_type VARCHAR(50) NOT NULL,
                    actor_name VARCHAR(100) NOT NULL,
                    entity_type VARCHAR(50) NOT NULL,
                    entity_id INTEGER,
                    old_value TEXT,
                    new_value TEXT,
                    metadata TEXT,
                    success BOOLEAN DEFAULT true NOT NULL,
                    error_message TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log (timestamp);
                CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_log (entity_type, entity_id);
                """
                db.session.execute(text(sql))
                db.session.commit()
                print("Table 'audit_log' created successfully.")
            else:
                print("Table 'audit_log' already exists.")
    except Exception as e:
        print(f"Manual table creation failed: {e}")

    # 3. Run Debug Script
    print("\n[3/3] Running Scoreboard Debugger...")
    try:
        with app.app_context():
            debug_scoreboard()
    except Exception as e:
        print(f"Debug script failed: {e}")

    # 4. Update Team Data
    print("\n[4/4] Updating Team Data...")
    try:
        from update_teams import update_teams
        update_teams()
        print("Team data update completed.")
    except Exception as e:
        print(f"Team data update failed: {e}")
    print("STARTUP TASKS COMPLETED")
    print("="*50 + "\n")

if __name__ == "__main__":
    run_startup()
