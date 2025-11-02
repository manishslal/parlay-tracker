#!/usr/bin/env python3
"""
Force ESPN API fetch for all historical bets and save to PostgreSQL
Run this once to populate all missing ESPN data
"""
from app import app, db, process_parlay_data
from models import Bet

def fetch_and_save_espn_data():
    """Fetch ESPN data for all historical bets and save to database"""
    
    print("🔄 Starting ESPN Data Fetch for Historical Bets\n")
    
    with app.app_context():
        # Get all completed bets
        completed_bets = Bet.query.filter_by(status='completed').all()
        print(f"📊 Found {len(completed_bets)} completed bets")
        
        # Convert to dict format for process_parlay_data
        parlays_to_process = []
        bet_objects = {}
        
        for bet in completed_bets:
            bet_data = bet.get_bet_data()
            bet_data['db_id'] = bet.id
            parlays_to_process.append(bet_data)
            bet_objects[bet.id] = bet
        
        print(f"🌐 Fetching ESPN data for {len(parlays_to_process)} bets...")
        print("⏳ This may take a few minutes...\n")
        
        # Process all bets through ESPN API
        try:
            processed_parlays = process_parlay_data(parlays_to_process)
            
            print(f"✅ ESPN fetch complete for {len(processed_parlays)} bets\n")
            
            # Save updated data back to database
            updated_count = 0
            no_data_count = 0
            
            for parlay in processed_parlays:
                bet_id = parlay.get('db_id')
                bet_obj = bet_objects.get(bet_id)
                
                if not bet_obj:
                    continue
                
                # Check if ESPN data was fetched
                has_espn_data = False
                for leg in parlay.get('legs', []):
                    if 'current' in leg and leg.get('current') != 0:
                        has_espn_data = True
                        break
                
                if has_espn_data:
                    # Save updated bet data
                    bet_obj.set_bet_data(parlay, preserve_status=True)
                    bet_obj.api_fetched = 'Yes'
                    updated_count += 1
                    print(f"  ✅ Updated: {parlay.get('name')}")
                else:
                    no_data_count += 1
                    print(f"  ⏭️  No ESPN data available: {parlay.get('name')} (game too old)")
            
            # Commit all changes
            db.session.commit()
            
            print(f"\n{'='*70}")
            print(f"✅ DATABASE UPDATE COMPLETE!")
            print('='*70)
            print(f"  ✅ Bets updated with ESPN data: {updated_count}")
            print(f"  ⏭️  Bets without ESPN data: {no_data_count}")
            print(f"  📊 Success rate: {updated_count/len(completed_bets)*100:.1f}%")
            print(f"\n💡 Refresh the Historical tab in your browser to see the updates!")
            
        except Exception as e:
            print(f"\n❌ Error during ESPN fetch: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    fetch_and_save_espn_data()
