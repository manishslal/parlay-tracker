#!/usr/bin/env python3
"""
Check database status and recent bets
"""
from app import app, db, Bet, User
from datetime import datetime

with app.app_context():
    # Get total counts
    total_bets = Bet.query.count()
    pending_bets = Bet.query.filter_by(status='pending').count()
    live_bets = Bet.query.filter_by(status='live').count()
    completed_bets = Bet.query.filter_by(status='completed').count()
    
    print(f"\n{'='*80}")
    print(f"DATABASE STATUS")
    print(f"{'='*80}")
    print(f"Total bets: {total_bets}")
    print(f"Pending: {pending_bets}")
    print(f"Live: {live_bets}")
    print(f"Completed: {completed_bets}")
    print(f"{'='*80}\n")
    
    # Get the most recent 5 bets
    recent_bets = Bet.query.order_by(Bet.id.desc()).limit(5).all()
    
    print(f"MOST RECENT 5 BETS:")
    print(f"{'-'*80}\n")
    
    for bet in recent_bets:
        bet_data = bet.get_bet_data()
        print(f"ID: {bet.id}")
        print(f"Bet ID: {bet_data.get('bet_id', 'N/A')}")
        print(f"Name: {bet_data.get('name', 'N/A')}")
        print(f"Status: {bet.status}")
        print(f"Active: {bet.is_active}")
        print(f"Wager: ${bet_data.get('wager', 0):.2f}")
        print(f"Payout: ${bet_data.get('potential_payout', 0):.2f}")
        print(f"Legs: {len(bet_data.get('legs', []))}")
        print(f"{'-'*80}\n")
    
    # Check if the two specific bets exist
    print(f"CHECKING FOR NEW BETS:")
    print(f"{'-'*80}\n")
    
    bet_64 = Bet.query.join(User).filter(Bet.bet_data.cast(db.String).like('%O/0240915/0000064%')).first()
    bet_65 = Bet.query.join(User).filter(Bet.bet_data.cast(db.String).like('%O/0240915/0000065%')).first()
    
    if bet_64:
        bet_data_64 = bet_64.get_bet_data()
        print(f"✅ Found bet O/0240915/0000064 (7 leg parlay)")
        print(f"   DB ID: {bet_64.id}")
        print(f"   Status: {bet_64.status}")
        print(f"   is_active: {bet_64.is_active}")
        print(f"   is_archived: {bet_64.is_archived}")
        print(f"   User ID: {bet_64.user_id}")
        print(f"   Wager: ${bet_data_64.get('wager', 0):.2f}")
    else:
        print(f"❌ Bet O/0240915/0000064 NOT FOUND")
    
    if bet_65:
        bet_data_65 = bet_65.get_bet_data()
        print(f"\n✅ Found bet O/0240915/0000065 (15 leg SGP+)")
        print(f"   DB ID: {bet_65.id}")
        print(f"   Status: {bet_65.status}")
        print(f"   is_active: {bet_65.is_active}")
        print(f"   is_archived: {bet_65.is_archived}")
        print(f"   User ID: {bet_65.user_id}")
        print(f"   Wager: ${bet_data_65.get('wager', 0):.2f}")
    else:
        print(f"❌ Bet O/0240915/0000065 NOT FOUND")
    
    # Check for bets with is_active filter
    print(f"\n{'-'*80}")
    print(f"ACTIVE BETS (is_active=True, is_archived=False):")
    print(f"{'-'*80}\n")
    active_bets = Bet.query.filter_by(is_active=True, is_archived=False).all()
    print(f"Total active bets: {len(active_bets)}")
    for bet in active_bets[:5]:
        bet_data = bet.get_bet_data()
        print(f"  - ID {bet.id}: {bet_data.get('name', 'N/A')} (Status: {bet.status})")
    
    print(f"\n{'='*80}\n")
