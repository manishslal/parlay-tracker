import logging
from datetime import datetime, timedelta
from app import app, db
from models import Player
from helpers.enhanced_player_search import enhanced_player_search
from helpers.espn_api import get_player_season_stats

logger = logging.getLogger(__name__)

def enrich_player_data():
    """
    Background job to:
    1. Find players with missing basic data (enrichment)
    2. Update season stats for players (stats update)
    """
    with app.app_context():
        logger.info("[PLAYER-ENRICHMENT] Starting player data enrichment job...")
        
        # 1. Basic Enrichment (Missing info)
        incomplete_players = Player.query.filter(
            (Player.position == None) | 
            (Player.jersey_number == None) | 
            (Player.current_team == None) | 
            (Player.current_team == '')
        ).limit(50).all()  # Limit to avoid timeouts
        
        # 2. Stats Update (Missing stats or old stats)
        # Prioritize players with ESPN ID but no stats
        stats_needed_players = Player.query.filter(
            Player.espn_player_id != None,
            (Player.season_stats == None) | 
            (Player.last_stats_update < datetime.utcnow() - timedelta(days=1))
        ).limit(50).all()
        
        # Combine lists (unique players)
        players_to_process = list(set(incomplete_players + stats_needed_players))
        
        if not players_to_process:
            logger.info("[PLAYER-ENRICHMENT] No players need updates.")
            return

        logger.info(f"[PLAYER-ENRICHMENT] Found {len(players_to_process)} players to process.")
        
        updated_count = 0
        
        for p in players_to_process:
            try:
                updated = False
                
                # Determine sport/league
                sport = "football" if p.sport == 'NFL' else "basketball"
                league = "nfl" if p.sport == 'NFL' else "nba"
                
                # --- Basic Enrichment ---
                if p in incomplete_players:
                    data = enhanced_player_search(p.player_name, sport=sport, league=league)
                    if data:
                        if p.sport != data['sport']:
                            p.sport = data['sport']
                            updated = True
                        if not p.position and data['position']:
                            p.position = data['position']
                            updated = True
                        
                        current_jersey = str(p.jersey_number) if p.jersey_number is not None else None
                        new_jersey = str(data['jersey_number']) if data['jersey_number'] is not None else None
                        if current_jersey != new_jersey and new_jersey:
                            try:
                                p.jersey_number = int(data['jersey_number'])
                                updated = True
                            except: pass

                        if (not p.current_team or p.current_team == '') and data['current_team']:
                            p.current_team = data['current_team']
                            updated = True
                        if (not p.team_abbreviation or p.team_abbreviation == '') and data['team_abbreviation']:
                            p.team_abbreviation = data['team_abbreviation']
                            updated = True
                        if (not p.espn_player_id or p.espn_player_id == '') and data['espn_player_id']:
                             p.espn_player_id = data['espn_player_id']
                             updated = True
                
                # --- Stats Update ---
                if p.espn_player_id:
                    # Refresh sport/league in case it changed
                    sport = "football" if p.sport == 'NFL' else "basketball"
                    league = "nfl" if p.sport == 'NFL' else "nba"
                    # Fetch stats
                    stats_data = get_player_season_stats(p.espn_player_id, sport=sport, league=league)
                    
                    if stats_data:
                        p.season_stats = stats_data.get('stats_season') # Keep for backward compatibility
                        # Merge new season stats with existing history
                        current_stats = p.stats_season or {}
                        # If current_stats is not a dict (legacy data), reset it
                        if not isinstance(current_stats, dict):
                            current_stats = {}
                        
                        # Update with new data (keyed by season year)
                        new_stats = stats_data.get('stats_season', {})
                        current_stats.update(new_stats)
                        
                        p.stats_season = current_stats
                        p.stats_last_5_games = stats_data.get('stats_last_5_games')
                        p.last_stats_update = datetime.utcnow()
                        
                        stats_updated_count += 1
                        updated = True # Mark as updated if stats were fetched
                        logger.info(f"[PLAYER-ENRICHMENT] Updated stats for {p.player_name}")

                if updated:
                    updated_count += 1
                
                # Commit every 10 updates or at the end of the loop
                if (updated_count + stats_updated_count) % 10 == 0:
                    db.session.commit()
            
            except Exception as e:
                logger.error(f"[PLAYER-ENRICHMENT] Error processing {p.player_name}: {e}")
                db.session.rollback()
        
        # Final commit for any remaining changes
        if updated_count > 0 or stats_updated_count > 0:
            db.session.commit()
                
        logger.info(f"[PLAYER-ENRICHMENT] Job completed. Updated {updated_count} players (including {stats_updated_count} with stats).")

        logger.info(f"[PLAYER-ENRICHMENT] Job completed. Updated {updated_count} players (including {stats_updated_count} with stats).")
