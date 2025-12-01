import logging
from app import app, db
from models import Player
from helpers.enhanced_player_search import enhanced_player_search

logger = logging.getLogger(__name__)

def enrich_player_data():
    """
    Background job to find players with missing data and attempt to enrich them
    using the enhanced player search (which now includes smart sport fallback).
    """
    with app.app_context():
        logger.info("[PLAYER-ENRICHMENT] Starting player data enrichment job...")
        
        # Find players with missing critical data
        incomplete_players = Player.query.filter(
            (Player.position == None) | 
            (Player.jersey_number == None) | 
            (Player.current_team == None) | 
            (Player.current_team == '')
        ).all()
        
        if not incomplete_players:
            logger.info("[PLAYER-ENRICHMENT] No incomplete players found.")
            return

        logger.info(f"[PLAYER-ENRICHMENT] Found {len(incomplete_players)} players to check.")
        
        updated_count = 0
        
        for p in incomplete_players:
            try:
                # Determine search parameters based on current (potentially wrong) sport
                sport = "football" if p.sport == 'NFL' else "basketball"
                league = "nfl" if p.sport == 'NFL' else "nba"
                
                # Search (will auto-fallback to other sport if needed)
                data = enhanced_player_search(p.player_name, sport=sport, league=league)
                
                if data:
                    updated = False
                    
                    # Update Sport
                    if p.sport != data['sport']:
                        logger.info(f"[PLAYER-ENRICHMENT] Updating Sport for {p.player_name}: {p.sport} -> {data['sport']}")
                        p.sport = data['sport']
                        updated = True
                    
                    # Update Position
                    if not p.position and data['position']:
                        p.position = data['position']
                        updated = True
                        
                    # Update Jersey
                    current_jersey = str(p.jersey_number) if p.jersey_number is not None else None
                    new_jersey = str(data['jersey_number']) if data['jersey_number'] is not None else None
                    
                    if current_jersey != new_jersey and new_jersey:
                        try:
                            p.jersey_number = int(data['jersey_number'])
                            updated = True
                        except:
                            pass

                    # Update Team
                    if (not p.current_team or p.current_team == '') and data['current_team']:
                        p.current_team = data['current_team']
                        updated = True
                        
                    # Update Team Abbr
                    if (not p.team_abbreviation or p.team_abbreviation == '') and data['team_abbreviation']:
                        p.team_abbreviation = data['team_abbreviation']
                        updated = True
                    
                    # Update ESPN ID
                    if (not p.espn_player_id or p.espn_player_id == '') and data['espn_player_id']:
                         p.espn_player_id = data['espn_player_id']
                         updated = True

                    if updated:
                        db.session.commit()
                        updated_count += 1
                        logger.info(f"[PLAYER-ENRICHMENT] Updated {p.player_name}")
            
            except Exception as e:
                logger.error(f"[PLAYER-ENRICHMENT] Error processing {p.player_name}: {e}")
                db.session.rollback()
                
        logger.info(f"[PLAYER-ENRICHMENT] Job completed. Updated {updated_count} players.")
