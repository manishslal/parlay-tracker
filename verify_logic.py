
import logging

# Mock class for BetLeg
class MockLeg:
    def __init__(self, id, bet_id, player_name, stat_type, bet_line_type, target_value, achieved_value, status, is_hit, game_status):
        self.id = id
        self.bet_id = bet_id
        self.player_name = player_name
        self.stat_type = stat_type
        self.bet_line_type = bet_line_type
        self.target_value = target_value
        self.achieved_value = achieved_value
        self.status = status
        self.is_hit = is_hit
        self.game_status = game_status
        self.leg_order = 1

def test_logic():
    # Test Case: Over bet that has hit (25 > 20)
    leg = MockLeg(
        id=1049,
        bet_id=187,
        player_name="Test Player",
        stat_type="points",
        bet_line_type="over",
        target_value=20.0,
        achieved_value=25.0,
        status="pending",
        is_hit=None,
        game_status="STATUS_IN_PROGRESS"
    )

    print(f"Initial State: Status={leg.status}, Is Hit={leg.is_hit}")

    # Logic from auto_determine_leg_hit_status
    is_hit = None
    stat_type = leg.stat_type.lower() if leg.stat_type else ''
    is_final = leg.game_status == 'STATUS_FINAL'
    
    if stat_type == 'moneyline':
        if is_final:
            is_hit = leg.achieved_value > 0
    elif stat_type == 'spread':
        if is_final and leg.target_value is not None:
            is_hit = (leg.achieved_value + leg.target_value) > 0
    else:
        if leg.target_value is not None:
            if leg.bet_line_type == 'under':
                if leg.achieved_value >= leg.target_value:
                    is_hit = False # Early Loss
                elif is_final:
                    is_hit = True # Final Win
            else:  
                # OVER bet
                if leg.achieved_value >= leg.target_value:
                    is_hit = True # Early Win
                elif is_final:
                    is_hit = False # Final Loss

    print(f"Calculated Is Hit: {is_hit}")
    
    if is_hit is not None:
        leg.is_hit = is_hit
        leg.status = 'won' if is_hit else 'lost'
        print(f"Final State: Status={leg.status}, Is Hit={leg.is_hit}")
    else:
        print("Final State: No Change")

if __name__ == "__main__":
    test_logic()
