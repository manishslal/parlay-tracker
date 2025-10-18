#!/usr/bin/env python3
"""Force compute returns for all parlays and overwrite returns field when computable.
This script writes Data/Historical_Bets.json, Data/Live_Bets.json, and Data/Todays_Bets.json.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HIST = ROOT / "Data" / "Historical_Bets.json"
LIVE = ROOT / "Data" / "Live_Bets.json"
TODAY = ROOT / "Data" / "Todays_Bets.json"


def _parse_american_odds(odds):
    if odds is None:
        return None
    try:
        s = str(odds).strip()
        if s == "":
            return None
        if s.startswith("+"):
            val = int(s[1:])
            return 1 + (val / 100.0)
        if s.startswith("-"):
            val = int(s[1:])
            if val == 0:
                return None
            return 1 + (100.0 / val)
        if s.isdigit() or (s[0] == '-' and s[1:].isdigit()):
            val = int(s)
            if val > 0:
                return 1 + (val / 100.0)
            else:
                return 1 + (100.0 / abs(val))
        f = float(s)
        if f > 0:
            return f
    except Exception:
        return None
    return None


def _compute_parlay_returns_from_odds(wager, parlay_odds=None, leg_odds_list=None):
    try:
        if wager is None:
            return None
        w = float(wager)
        if parlay_odds:
            mult = _parse_american_odds(parlay_odds)
            if mult is None:
                return None
            return round(w * (mult - 1), 2)
        if leg_odds_list:
            mult = 1.0
            any_parsed = False
            for o in leg_odds_list:
                pm = _parse_american_odds(o)
                if pm is None:
                    continue
                any_parsed = True
                mult *= pm
            if any_parsed:
                return round(w * (mult - 1), 2)
        return None
    except Exception:
        return None


def force_update(path: Path):
    if not path.exists():
        return []
    data = json.loads(path.read_text())
    updated = []
    for parlay in data:
        parlay_odds = parlay.get('odds')
        parlay_wager = parlay.get('wager')
        leg_odds = [l.get('odds') for l in parlay.get('legs', []) if l.get('odds') is not None]
        val = _compute_parlay_returns_from_odds(parlay_wager, parlay_odds, leg_odds)
        if val is not None:
            parlay['returns'] = val
            updated.append((parlay.get('name'), val))
    path.write_text(json.dumps(data, indent=2))
    return updated


def main():
    results = {}
    for p in [HIST, LIVE, TODAY]:
        results[p.name] = force_update(p)
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
#!/usr/bin/env python3
"""Force compute returns for all parlays and overwrite returns field when computable.
This is like the previous script but always attempts to compute (useful if previous runs were blocked by server writes).
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HIST = ROOT / "Historical_Bets.json"
LIVE = ROOT / "Live_Bets.json"
TODAY = ROOT / "Todays_Bets.json"


def _parse_american_odds(odds):
    if odds is None:
        return None
    try:
        s = str(odds).strip()
        if s == "":
            return None
        if s.startswith("+"):
            val = int(s[1:])
            return 1 + (val / 100.0)
        if s.startswith("-"):
            val = int(s[1:])
            if val == 0:
                return None
            return 1 + (100.0 / val)
        if s.isdigit() or (s[0] == '-' and s[1:].isdigit()):
            val = int(s)
            if val > 0:
                return 1 + (val / 100.0)
            else:
                return 1 + (100.0 / abs(val))
        f = float(s)
        if f > 0:
            return f
    except Exception:
        return None
    return None


def _compute_parlay_returns_from_odds(wager, parlay_odds=None, leg_odds_list=None):
    try:
        if wager is None:
            return None
        w = float(wager)
        if parlay_odds:
            mult = _parse_american_odds(parlay_odds)
            if mult is None:
                return None
            return round(w * (mult - 1), 2)
        if leg_odds_list:
            mult = 1.0
            any_parsed = False
            for o in leg_odds_list:
                pm = _parse_american_odds(o)
                if pm is None:
                    continue
                any_parsed = True
                mult *= pm
            if any_parsed:
                return round(w * (mult - 1), 2)
        return None
    except Exception:
        return None


def force_update(path: Path):
    if not path.exists():
        return []
    data = json.loads(path.read_text())
    updated = []
    for parlay in data:
        parlay_odds = parlay.get('odds')
        parlay_wager = parlay.get('wager')
        leg_odds = [l.get('odds') for l in parlay.get('legs', []) if l.get('odds') is not None]
        val = _compute_parlay_returns_from_odds(parlay_wager, parlay_odds, leg_odds)
        if val is not None:
            parlay['returns'] = val
            updated.append((parlay.get('name'), val))
    path.write_text(json.dumps(data, indent=2))
    return updated


def main():
    results = {}
    for p in [HIST, LIVE, TODAY]:
        results[p.name] = force_update(p)
    print(json.dumps(results, indent=2))

if __name__ == '__main__':
    main()
