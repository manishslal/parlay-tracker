
from models import db

class BetLeg(db.Model):
    __tablename__ = 'bet_legs'  # Use the correct table name
    
    id = db.Column(db.Integer, primary_key=True)
    bet_id = db.Column(db.Integer, db.ForeignKey('bets.id'))
    player_id = db.Column(db.Integer, db.ForeignKey('players.id'))

    # Player/Team Info (Denormalized for performance)
    player_name = db.Column(db.String(100), nullable=False)
    player_team = db.Column(db.String(50))
    player_position = db.Column(db.String(10))

    # Game Info
    home_team = db.Column(db.String(50), nullable=False)
    away_team = db.Column(db.String(50), nullable=False)
    game_id = db.Column(db.String(50))
    game_date = db.Column(db.Date)
    game_time = db.Column(db.Time)
    game_status = db.Column(db.String(20))
    sport = db.Column(db.String(50))
    parlay_sport = db.Column(db.String(50))

    # Bet Details
    bet_type = db.Column(db.String(50), nullable=False)
    stat_type = db.Column(db.String(50))  # Moved here, increased size
    bet_line_type = db.Column(db.String(20))  # 'over', 'under', NULL
    target_value = db.Column(db.Numeric(10, 2), nullable=False)
    achieved_value = db.Column(db.Numeric(10, 2))

    # Performance Comparison
    player_season_avg = db.Column(db.Numeric(10, 2))
    player_last_5_avg = db.Column(db.Numeric(10, 2))
    vs_opponent_avg = db.Column(db.Numeric(10, 2))
    target_vs_season = db.Column(db.Numeric(10, 2))

    # Odds Tracking
    original_leg_odds = db.Column(db.Integer)
    boosted_leg_odds = db.Column(db.Integer)
    final_leg_odds = db.Column(db.Integer)

    # Leg Status
    status = db.Column(db.String(20), default='pending')
    is_hit = db.Column(db.Boolean)
    void_reason = db.Column(db.String(100))

    # Live Game Data
    current_quarter = db.Column(db.String(10))
    time_remaining = db.Column(db.String(20))
    home_score = db.Column(db.Integer)
    away_score = db.Column(db.Integer)

    # Contextual Data
    is_home_game = db.Column(db.Boolean)
    weather_conditions = db.Column(db.String(100))
    injury_during_game = db.Column(db.Boolean, default=False)
    dnp_reason = db.Column(db.String(100))

    # Metadata
    leg_order = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

    def get_display_values(self):
        """Calculate display values for Current and Progress fields for moneyline, spread, and total_points bets."""
        current_display = None
        progress_display = None
        progress_color = None
        
        # Only calculate for moneyline, spread, and total_points bets
        if self.stat_type and self.stat_type.lower() in ['moneyline', 'spread', 'total_points']:
            # Determine bet team and opponent
            bet_team = self.player_name or self.player_team or ''
            is_home_bet = self.is_home_game
            
            # Get scores
            home_score = self.home_score or 0
            away_score = self.away_score or 0
            
            # Calculate score differential from bet team's perspective
            if is_home_bet:
                score_diff = home_score - away_score
                bet_score = home_score
                opp_score = away_score
                opp_team = self.away_team
            else:
                score_diff = away_score - home_score
                bet_score = away_score
                opp_score = home_score
                opp_team = self.home_team
            
            # Progress display: "BET_TEAM SCORE - OPP_SCORE OPP_TEAM"
            progress_display = f"{bet_team} {bet_score} - {opp_score} {opp_team}"
            
            if self.stat_type.lower() == 'moneyline':
                if self.status in ['won', 'lost']:
                    # For completed games, show Win/Loss
                    current_display = "Win" if self.status == 'won' else "Loss"
                    progress_color = "green" if self.status == 'won' else "red"
                elif self.status == 'pending' and self.home_score is not None and self.away_score is not None:
                    # For pending games, show Up/Down
                    if score_diff > 0:
                        current_display = f"Up {score_diff}"
                        progress_color = "green"
                    elif score_diff < 0:
                        current_display = f"Down {abs(score_diff)}"
                        progress_color = "red"
                    else:
                        current_display = "Even"
                        progress_color = "yellow"
                        
            elif self.stat_type.lower() == 'spread':
                spread_value = self.target_value or 0
                if self.status in ['won', 'lost']:
                    # For completed games, show the spread result
                    current_display = f"{'+' if self.is_hit else '-'}{abs(spread_value)}"
                    progress_color = "green" if self.status == 'won' else "red"
                elif self.status == 'pending' and self.home_score is not None and self.away_score is not None:
                    # For pending games, show current spread status
                    # Positive spread_diff means covering, negative means not covering
                    spread_diff = score_diff + spread_value
                    if spread_diff > 0:
                        current_display = f"+{spread_diff}"
                        progress_color = "green"
                    elif spread_diff < 0:
                        current_display = f"{spread_diff}"
                        progress_color = "red"
                    else:
                        current_display = "Push"
                        progress_color = "yellow"
                        
            elif self.stat_type.lower() == 'total_points':
                target_total = self.target_value or 0
                actual_total = (self.home_score or 0) + (self.away_score or 0)
                
                # Progress display: "AWAY_TEAM SCORE - HOME_TEAM SCORE (TOTAL)"
                progress_display = f"{self.away_team} {self.away_score or 0} - {self.home_team} {self.home_score or 0} ({actual_total})"
                
                if self.status in ['won', 'lost']:
                    # For completed games, show Over/Under result
                    if self.bet_line_type and 'over' in self.bet_line_type.lower():
                        current_display = f"Over {target_total}"
                    elif self.bet_line_type and 'under' in self.bet_line_type.lower():
                        current_display = f"Under {target_total}"
                    else:
                        current_display = f"{'Over' if actual_total > target_total else 'Under'} {target_total}"
                    
                    # Color based on win/loss
                    progress_color = "green" if self.status == 'won' else "red"
                    
                elif self.status == 'pending' and self.home_score is not None and self.away_score is not None:
                    # For pending games, show current total vs target
                    total_diff = actual_total - target_total
                    if total_diff > 0:
                        current_display = f"+{total_diff}"
                        progress_color = "green" if (self.bet_line_type and 'over' in self.bet_line_type.lower()) else "red"
                    elif total_diff < 0:
                        current_display = f"{total_diff}"
                        progress_color = "red" if (self.bet_line_type and 'over' in self.bet_line_type.lower()) else "green"
                    else:
                        current_display = "Push"
                        progress_color = "yellow"
        
        return {
            'current_display': current_display,
            'progress_display': progress_display,
            'progress_color': progress_color
        }

    def to_dict(self):
        base_dict = {
            'id': self.id,
            'bet_id': self.bet_id,
            'player_id': self.player_id,
            'player': self.player_name,  # Frontend expects 'player'
            'player_name': self.player_name,
            'player_team': self.player_team,
            'team': self.player_team,  # Frontend expects 'team'
            'player_position': self.player_position,
            'position': self.player_position,  # Frontend expects 'position'
            'home': self.home_team,  # Frontend expects 'home'
            'home_team': self.home_team,
            'away': self.away_team,  # Frontend expects 'away'
            'away_team': self.away_team,
            'game_id': self.game_id,
            'game_date': self.game_date.isoformat() if self.game_date else None,
            'game_time': self.game_time.isoformat() if self.game_time else None,
            'gameStatus': self.game_status,  # Frontend expects 'gameStatus'
            'score_diff': (self.home_score - self.away_score) if (self.home_score is not None and self.away_score is not None) else None,  # Frontend expects 'score_diff'
            'sport': self.sport,
            'parlay_sport': self.parlay_sport,
            'bet_type': self.bet_type,
            'stat': self.stat_type,  # Frontend expects 'stat'
            'stat_type': self.stat_type,
            'bet_line_type': self.bet_line_type,
            'over_under': self.bet_line_type,  # Frontend expects 'over_under'
            'stat_add': self.bet_line_type,  # Frontend expects 'stat_add'
            'target': float(self.target_value) if self.target_value else None,  # Frontend expects 'target'
            'target_value': float(self.target_value) if self.target_value else None,
            'current': float(self.achieved_value) if self.achieved_value else None,  # Frontend expects 'current'
            'achieved_value': float(self.achieved_value) if self.achieved_value else None,
            'player_season_avg': float(self.player_season_avg) if self.player_season_avg else None,
            'player_last_5_avg': float(self.player_last_5_avg) if self.player_last_5_avg else None,
            'vs_opponent_avg': float(self.vs_opponent_avg) if self.vs_opponent_avg else None,
            'target_vs_season': float(self.target_vs_season) if self.target_vs_season else None,
            'original_leg_odds': self.original_leg_odds,
            'boosted_leg_odds': self.boosted_leg_odds,
            'final_leg_odds': self.final_leg_odds,
            'status': self.status,
            'is_hit': self.is_hit,
            'void_reason': self.void_reason,
            'current_quarter': self.current_quarter,
            'time_remaining': self.time_remaining,
            'home_score': self.home_score,
            'away_score': self.away_score,
            'homeScore': self.home_score,  # Frontend expects camelCase
            'awayScore': self.away_score,  # Frontend expects camelCase
            'is_home_game': self.is_home_game,
            'weather_conditions': self.weather_conditions,
            'injury_during_game': self.injury_during_game,
            'dnp_reason': self.dnp_reason,
            'leg_order': self.leg_order,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        
        # Add display values for moneyline and spread bets
        display_values = self.get_display_values()
        base_dict.update(display_values)
        
        return base_dict

    def get_display_values(self):
        """Calculate display values for Current and Progress fields for moneyline and spread bets."""
        current_display = None
        progress_display = None
        progress_color = None
        
        # Only calculate for moneyline and spread bets
        if self.stat_type and self.stat_type.lower() in ['moneyline', 'spread', 'total_points']:
            # Get scores
            home_score = self.home_score or 0
            away_score = self.away_score or 0
            
            # For moneyline bets, determine bet team and opponent based on player_team
            if self.stat_type.lower() == 'moneyline':
                bet_team = self.player_team or self.player_name or ''
                # Determine if bet team is home or away
                if bet_team and self.home_team and bet_team.lower() in self.home_team.lower():
                    # Bet is on home team
                    bet_score = home_score
                    opp_score = away_score
                    opp_team = self.away_team
                    score_diff = home_score - away_score
                elif bet_team and self.away_team and bet_team.lower() in self.away_team.lower():
                    # Bet is on away team
                    bet_score = away_score
                    opp_score = home_score
                    opp_team = self.home_team
                    score_diff = away_score - home_score
                else:
                    # Fallback: use is_home_game if team matching fails
                    bet_team = self.player_name or self.player_team or ''
                    is_home_bet = self.is_home_game
                    if is_home_bet:
                        score_diff = home_score - away_score
                        bet_score = home_score
                        opp_score = away_score
                        opp_team = self.away_team
                    else:
                        score_diff = away_score - home_score
                        bet_score = away_score
                        opp_score = home_score
                        opp_team = self.home_team
            else:
                # For spread and total_points, use the original logic
                bet_team = self.player_name or self.player_team or ''
                is_home_bet = self.is_home_game
                
                # Calculate score differential from bet team's perspective
                if is_home_bet:
                    score_diff = home_score - away_score
                    bet_score = home_score
                    opp_score = away_score
                    opp_team = self.away_team
                else:
                    score_diff = away_score - home_score
                    bet_score = away_score
                    opp_score = home_score
                    opp_team = self.home_team
            
            # Progress display: "BET_TEAM SCORE - OPP_SCORE OPP_TEAM"
            progress_display = f"{bet_team} {bet_score} - {opp_score} {opp_team}"
            
            if self.stat_type.lower() == 'moneyline':
                if self.status in ['won', 'lost']:
                    # For completed games, show Win/Loss
                    current_display = "Win" if self.status == 'won' else "Loss"
                    progress_color = "green" if self.status == 'won' else "red"
                elif self.status == 'pending' and self.home_score is not None and self.away_score is not None:
                    # For pending games, show Up/Down
                    if score_diff > 0:
                        current_display = f"Up {score_diff}"
                        progress_color = "green"
                    elif score_diff < 0:
                        current_display = f"Down {abs(score_diff)}"
                        progress_color = "red"
                    else:
                        current_display = "Even"
                        progress_color = "yellow"
            elif self.stat_type.lower() == 'total_points':
                target_total = self.target_value or 0
                actual_total = (self.home_score or 0) + (self.away_score or 0)
                
                # Progress display: "AWAY_TEAM SCORE - HOME_TEAM SCORE (TOTAL)"
                progress_display = f"{self.away_team} {self.away_score or 0} - {self.home_team} {self.home_score or 0} ({actual_total})"
                
                if self.status in ['won', 'lost']:
                    # For completed games, show Over/Under result
                    if self.bet_line_type and 'over' in self.bet_line_type.lower():
                        current_display = f"Over {target_total}"
                    elif self.bet_line_type and 'under' in self.bet_line_type.lower():
                        current_display = f"Under {target_total}"
                    else:
                        current_display = f"{'Over' if actual_total > target_total else 'Under'} {target_total}"
                    
                    # Color based on win/loss
                    progress_color = "green" if self.status == 'won' else "red"
                    
                elif self.status == 'pending' and self.home_score is not None and self.away_score is not None:
                    # For pending games, show current total vs target
                    total_diff = actual_total - target_total
                    if total_diff > 0:
                        current_display = f"+{total_diff}"
                        progress_color = "green" if (self.bet_line_type and 'over' in self.bet_line_type.lower()) else "red"
                    elif total_diff < 0:
                        current_display = f"{total_diff}"
                        progress_color = "red" if (self.bet_line_type and 'over' in self.bet_line_type.lower()) else "green"
                    else:
                        current_display = "Push"
                        progress_color = "yellow"
            
            elif self.stat_type.lower() == 'spread':
                spread_value = self.target_value or 0
                if self.status in ['won', 'lost']:
                    # For completed games, show the spread result
                    current_display = f"{'+' if self.is_hit else '-'}{abs(spread_value)}"
                    progress_color = "green" if self.status == 'won' else "red"
                elif self.status == 'pending' and self.home_score is not None and self.away_score is not None:
                    # For pending games, show current spread status
                    # Positive spread_diff means covering, negative means not covering
                    spread_diff = score_diff + spread_value
                    if spread_diff > 0:
                        current_display = f"+{spread_diff}"
                        progress_color = "green"
                    elif spread_diff < 0:
                        current_display = f"{spread_diff}"
                        progress_color = "red"
                    else:
                        current_display = "Push"
                        progress_color = "yellow"
            elif self.stat_type.lower() == 'total_points':
                target_total = self.target_value or 0
                actual_total = (self.home_score or 0) + (self.away_score or 0)
                
                # Progress display: "AWAY_TEAM SCORE - HOME_TEAM SCORE (TOTAL)"
                progress_display = f"{self.away_team} {self.away_score or 0} - {self.home_team} {self.home_score or 0} ({actual_total})"
                
                if self.status in ['won', 'lost']:
                    # For completed games, show Over/Under result
                    if self.bet_line_type and 'over' in self.bet_line_type.lower():
                        current_display = f"Over {target_total}"
                    elif self.bet_line_type and 'under' in self.bet_line_type.lower():
                        current_display = f"Under {target_total}"
                    else:
                        current_display = f"{'Over' if actual_total > target_total else 'Under'} {target_total}"
                    
                    # Color based on win/loss
                    progress_color = "green" if self.status == 'won' else "red"
                    
                elif self.status == 'pending' and self.home_score is not None and self.away_score is not None:
                    # For pending games, show current total vs target
                    total_diff = actual_total - target_total
                    if total_diff > 0:
                        current_display = f"+{total_diff}"
                        progress_color = "green" if (self.bet_line_type and 'over' in self.bet_line_type.lower()) else "red"
                    elif total_diff < 0:
                        current_display = f"{total_diff}"
                        progress_color = "red" if (self.bet_line_type and 'over' in self.bet_line_type.lower()) else "green"
                    else:
                        current_display = "Push"
                        progress_color = "yellow"
        
        return {
            'current_display': current_display,
            'progress_display': progress_display,
            'progress_color': progress_color
        }
