
from models import db
import json


class Bet(db.Model):
    __tablename__ = 'bets'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    betting_site_id = db.Column(db.String(100))
    bet_type = db.Column(db.String(50))
    betting_site = db.Column(db.String(50))
    status = db.Column(db.String(20))
    is_active = db.Column(db.Boolean)
    is_archived = db.Column(db.Boolean)
    api_fetched = db.Column(db.String(3))
    bet_data = db.Column(db.Text)
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)
    bet_date = db.Column(db.String(20))
    wager = db.Column(db.Numeric(10, 2))
    original_odds = db.Column(db.Integer)
    boosted_odds = db.Column(db.Integer)
    final_odds = db.Column(db.Integer)
    is_boosted = db.Column(db.Boolean)
    potential_winnings = db.Column(db.Numeric(10, 2))
    actual_winnings = db.Column(db.Numeric(10, 2))
    has_insurance = db.Column(db.Boolean)
    insurance_type = db.Column(db.String(50))
    insurance_amount = db.Column(db.Numeric(10, 2))
    insurance_triggered = db.Column(db.Boolean)
    total_legs = db.Column(db.Integer)
    legs_won = db.Column(db.Integer)
    legs_lost = db.Column(db.Integer)
    legs_pending = db.Column(db.Integer)
    legs_live = db.Column(db.Integer)
    legs_void = db.Column(db.Integer)
    last_api_update = db.Column(db.DateTime)
    secondary_bettors = db.Column(db.ARRAY(db.Integer))
    watchers = db.Column(db.ARRAY(db.Integer))
    bet_legs_rel = db.relationship('BetLeg', backref='bet', lazy=True)

    __mapper_args__ = {
        'include_properties': [
            'id', 'user_id', 'betting_site_id', 'bet_type', 'betting_site', 'status',
            'is_active', 'is_archived', 'api_fetched', 'bet_data', 'created_at', 'updated_at',
            'bet_date', 'wager', 'original_odds', 'boosted_odds', 'final_odds', 'is_boosted',
            'potential_winnings', 'actual_winnings', 'has_insurance', 'insurance_type',
            'insurance_amount', 'insurance_triggered', 'total_legs', 'legs_won', 'legs_lost',
            'legs_pending', 'legs_live', 'legs_void', 'last_api_update', 'secondary_bettors', 'watchers'
        ]
    }

    def get_bet_data(self):
        import json
        data = {}
        if self.bet_data:
            try:
                data = json.loads(self.bet_data)
            except Exception:
                data = {}
        
        # Include legs from database relationship if not already in bet_data
        if 'legs' not in data and self.bet_legs_rel:
            data['legs'] = [leg.to_dict() for leg in sorted(self.bet_legs_rel, key=lambda x: x.leg_order or 0)]
        
        return data

    def to_dict_structured(self, use_live_data=False):
        result = {
            'db_id': self.id,
            'betting_site_id': self.betting_site_id,
            'user_id': self.user_id,
            'bet_type': self.bet_type,
            'betting_site': self.betting_site,
            'status': self.status,
            'is_active': self.is_active,
            'is_archived': self.is_archived,
            'api_fetched': self.api_fetched,
            'bet_data': self.bet_data,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'bet_date': self.bet_date,
            'wager': float(self.wager) if self.wager is not None else None,
            'original_odds': self.original_odds,
            'boosted_odds': self.boosted_odds,
            'final_odds': self.final_odds,
            'is_boosted': self.is_boosted,
            'potential_winnings': float(self.potential_winnings) if self.potential_winnings is not None else None,
            'actual_winnings': float(self.actual_winnings) if self.actual_winnings is not None else None,
            'has_insurance': self.has_insurance,
            'insurance_type': self.insurance_type,
            'insurance_amount': float(self.insurance_amount) if self.insurance_amount is not None else None,
            'insurance_triggered': self.insurance_triggered,
            'total_legs': self.total_legs,
            'legs_won': self.legs_won,
            'legs_lost': self.legs_lost,
            'legs_pending': self.legs_pending,
            'legs_live': self.legs_live,
            'legs_void': self.legs_void,
            'last_api_update': self.last_api_update,
            'secondary_bettors': self.secondary_bettors,
            'watchers': self.watchers,
            # Add more fields as needed
        }
        
        # Add name field for process_parlay_data compatibility
        if self.bet_type == 'SGP':
            result['name'] = f"{self.total_legs} Leg SGP"
        elif self.bet_type == 'Parlay':
            result['name'] = f"{self.total_legs} Pick Parlay"
        else:
            result['name'] = self.bet_type or 'Parlay'
        
        # Add aliases for process_parlay_data compatibility
        result['odds'] = self.final_odds
        result['returns'] = float(self.potential_winnings) if self.potential_winnings is not None else 0
        
        # Include legs from database relationship
        if self.bet_legs_rel:
            result['legs'] = [leg.to_dict() for leg in sorted(self.bet_legs_rel, key=lambda x: x.leg_order or 0)]
        else:
            result['legs'] = []
            
        # Create games array from leg data for both live and historical bets
        # This ensures the frontend always has game status information
        if 'games' not in result:
            from models import Team
            games_map = {}
            for leg in result['legs']:
                if leg.get('home_team') and leg.get('away_team'):
                    game_key = f"{leg['away_team']}-{leg['home_team']}"
                    if game_key not in games_map:
                        # Look up team abbreviations from teams table using partial matching
                        home_team_obj = Team.query.filter(Team.team_name.ilike(f'%{leg["home_team"]}%')).first()
                        away_team_obj = Team.query.filter(Team.team_name.ilike(f'%{leg["away_team"]}%')).first()
                        
                        home_abbr = home_team_obj.team_abbr if home_team_obj else leg['home_team'][:3].upper()
                        away_abbr = away_team_obj.team_abbr if away_team_obj else leg['away_team'][:3].upper()
                        
                        # Determine game status - use actual database status for live/historical
                        # For live bets: use game_status from leg (STATUS_IN_PROGRESS, STATUS_FINAL, etc.)
                        # For historical bets: use gameStatus field or STATUS_FINAL
                        game_status = leg.get('game_status') or leg.get('gameStatus') or 'STATUS_SCHEDULED'
                        
                        # Create mock game object with scores
                        # Use full team names for matching with leg data
                        mock_game = {
                            'teams': {
                                'home': leg['home_team'],  # Use full name for frontend matching
                                'away': leg['away_team'],   # Use full name for frontend matching
                                'home_abbr': home_abbr,     # Store abbreviation for display
                                'away_abbr': away_abbr      # Store abbreviation for display
                            },
                            'score': {
                                'home': leg.get('home_score', 0) or leg.get('homeScore', 0),
                                'away': leg.get('away_score', 0) or leg.get('awayScore', 0)
                            },
                            'statusTypeName': game_status,
                            'game_date': leg.get('game_date', ''),
                            'startDateTime': leg.get('game_date', ''),
                            'period': leg.get('current_quarter', ''),
                            'clock': leg.get('time_remaining', '')
                        }
                        games_map[game_key] = mock_game
            result['games'] = list(games_map.values())
            
        return result

    def set_bet_data(self, bet_dict, preserve_status=False):
        """Store bet data as JSON string
        
        Args:
            bet_dict: Dictionary containing bet data
            preserve_status: If True, don't recalculate status from legs (useful during migration)
        """
        self.bet_data = json.dumps(bet_dict)
        
        # Extract commonly queried fields - maps to Bet table columns
        self.betting_site_id = bet_dict.get('bet_id', '')
        self.bet_type = bet_dict.get('type', 'parlay')  # bet_dict['type'] -> bets.bet_type
        self.betting_site = bet_dict.get('betting_site', 'Unknown')
        self.bet_date = bet_dict.get('bet_date', '')
        
        # Extract structured financial data - maps to Bet table columns
        self.wager = bet_dict.get('wager') or bet_dict.get('stake')  # Support both field names
        self.potential_winnings = bet_dict.get('potential_winnings') or bet_dict.get('potential_return')
        
        # Handle final_odds (can be string like "+450" or integer)
        final_odds_value = bet_dict.get('final_odds') or bet_dict.get('american_odds')
        if final_odds_value:
            # If it's a string like "+450" or "-110", try to parse the integer
            if isinstance(final_odds_value, str):
                try:
                    # Remove + or - and parse
                    odds_str = final_odds_value.strip()
                    if odds_str.startswith('+') or odds_str.startswith('-'):
                        self.final_odds = int(odds_str.replace('+', ''))
                    else:
                        self.final_odds = int(odds_str)
                except (ValueError, AttributeError):
                    self.final_odds = None
            else:
                self.final_odds = final_odds_value
        
        # Count legs for structured columns
        legs = bet_dict.get('legs', [])
        self.total_legs = len(legs)
        if legs:
            self.legs_won = sum(1 for leg in legs if leg.get('status') == 'won')
            self.legs_lost = sum(1 for leg in legs if leg.get('status') == 'lost')
            self.legs_pending = sum(1 for leg in legs if leg.get('status') == 'pending')
            self.legs_live = sum(1 for leg in legs if leg.get('status') == 'live')
            self.legs_void = sum(1 for leg in legs if leg.get('status') == 'void')
        
        # Only recalculate status if not preserving existing status
        if not preserve_status:
            # Determine status from legs if present
            if legs:
                if all(leg.get('status') == 'won' for leg in legs):
                    self.status = 'won'
                elif any(leg.get('status') == 'lost' for leg in legs):
                    self.status = 'lost'
                elif any(leg.get('status') == 'live' for leg in legs):
                    self.status = 'live'
                else:
                    self.status = 'pending'

    def to_dict(self):
        """Alias for to_dict_structured for backward compatibility"""
        return self.to_dict_structured()
