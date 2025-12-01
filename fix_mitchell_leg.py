from app import app, db
from models import BetLeg

def fix_mitchell_leg():
    print("Fixing Mitchell's leg...")
    with app.app_context():
        # Find Mitchell's leg in bet 6
        leg = BetLeg.query.filter(
            BetLeg.bet_id == 6,
            BetLeg.player_name.like('%Mitchell%')
        ).first()
        
        if not leg:
            print("Mitchell's leg not found")
            return
        
        print(f"Current: {leg.player_name} - {leg.stat_type}")
        print(f"  Status: {leg.status}")
        print(f"  Is Hit: {leg.is_hit}")
        print(f"  Achieved: {leg.achieved_value}, Target: {leg.target_value}")
        
        # Fix the status
        if leg.achieved_value and leg.target_value:
            is_hit = leg.achieved_value >= leg.target_value
            leg.is_hit = is_hit
            leg.status = 'won' if is_hit else 'lost'
            
            db.session.commit()
            print(f"\n✅ Updated:")
            print(f"  Status: {leg.status}")
            print(f"  Is Hit: {leg.is_hit}")

if __name__ == "__main__":
    fix_mitchell_leg()
