import pytest
from helpers.utils import parse_american_odds, compute_parlay_returns_from_odds


def test_parse_positive_american():
    assert parse_american_odds("+150") == pytest.approx(2.5)
    assert parse_american_odds("+100") == pytest.approx(2.0)


def test_parse_negative_american():
    assert parse_american_odds("-100") is None or parse_american_odds("-100") == pytest.approx(2.0)
    # -200 should be 1 + 100/200 = 1.5
    assert parse_american_odds("-200") == pytest.approx(1.5)


def test_parse_decimal():
    assert parse_american_odds("1.75") == pytest.approx(1.75)


def test_compute_parlay_from_parlay_odds():
    assert compute_parlay_returns_from_odds(10, parlay_odds="+500") == pytest.approx(50.0)


def test_compute_parlay_from_leg_odds():
    # +200 and +150 -> multipliers 3.0 and 2.5 => combined 7.5 => profit = 10*(7.5-1)=65.0
    assert compute_parlay_returns_from_odds(10, leg_odds_list=["+200", "+150"]) == pytest.approx(65.0)
