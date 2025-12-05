
from app import app, db
from models import BetLeg
from stat_standardization import standardize_stat_type

def fix_existing_atd_bets():
    with app.app_context():
        print("Checking for existing ATD bets with target_value=0...")
        
        # Get all pending/live legs
        legs = BetLeg.query.filter(
            BetLeg.status.in_(['pending', 'live'])
        ).all()
        
        updated_count = 0
        
        for leg in legs:
            # Standardize stat type if needed (though it should be stored standardized)
            # But let's check the stored value
            stat_std = standardize_stat_type(leg.stat_type, sport=leg.sport)
            
            if stat_std == 'anytime_touchdown':
                if not leg.target_value or leg.target_value == 0:
                    print(f"Fixing Leg {leg.id} ({leg.player_name}): target {leg.target_value} -> 1.0")
                    leg.target_value = 1.0
                    updated_count += 1
        
        if updated_count > 0:
            db.session.commit()
            print(f"✅ Successfully updated {updated_count} ATD bets.")
        else:
            print("No ATD bets needed fixing.")

if __name__ == "__main__":
    fix_existing_atd_bets()
