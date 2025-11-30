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

    # 2. Run Debug Script
    print("\n[2/2] Running Scoreboard Debugger...")
    try:
        with app.app_context():
            debug_scoreboard()
    except Exception as e:
        print(f"Debug script failed: {e}")
        
    print("\n" + "="*50)
    print("STARTUP TASKS COMPLETED")
    print("="*50 + "\n")

if __name__ == "__main__":
    run_startup()
