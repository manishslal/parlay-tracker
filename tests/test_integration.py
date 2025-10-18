import json
import pytest
import sys
from pathlib import Path
# Ensure project root is on sys.path so `from app import app` works under pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_historical_values(client):
    resp = client.get('/historical')
    assert resp.status_code == 200
    data = resp.get_json()
    # Find legs for Tyler Allgeier and Jacory Croskey-Merritt
    tyler_td = None
    jacory_rush = None
    for parlay in data:
        for leg in parlay.get('legs', []):
            if leg.get('player') == 'Tyler Allgeier' and leg.get('stat') == 'anytime_touchdown':
                tyler_td = leg.get('current')
            if leg.get('player') == 'Jacory Croskey-Merritt' and leg.get('stat') in ('rushing_yards_alt','rushing_yards'):
                jacory_rush = leg.get('current')
    assert tyler_td == 1, f"Expected Tyler Allgeier TD == 1, got {tyler_td}"
    assert jacory_rush == 61, f"Expected Jacory Croskey-Merritt rush == 61, got {jacory_rush}"
