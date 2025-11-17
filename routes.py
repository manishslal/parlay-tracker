from flask import Blueprint, jsonify, request, session
from typing import Any
from flask_login import login_required, current_user
from models import db, Bet
from services import get_user_bets_query, process_parlay_data, has_complete_final_data, save_final_results_to_bet, auto_move_completed_bets, sort_parlays_by_date


# ============================================================================
# Admin Endpoints
# ============================================================================

# ============================================================================
# API Endpoints
# ============================================================================

# All bet-related routes have been moved to routes/bets.py
