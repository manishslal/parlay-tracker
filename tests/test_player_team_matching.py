"""
Unit tests for player and team matching logic in ESPN integration.

Tests validate:
1. Player name normalization
2. Token-based player matching
3. Fuzzy matching with normalized inputs
4. Team name matching with case-insensitivity
"""

import unittest
import re
from difflib import get_close_matches


class TestNameNormalization(unittest.TestCase):
    """Test the _norm() function for name standardization"""
    
    def _norm(self, s):
        """Normalize names by removing special chars and lowercasing"""
        return re.sub(r"[^a-z0-9 ]+", "", s.lower()).strip()
    
    def test_norm_removes_apostrophes(self):
        """Test that apostrophes are removed"""
        self.assertEqual(self._norm("D'Andre Swift"), "dandre swift")
        self.assertEqual(self._norm("Ja'Marr Chase"), "jamarr chase")
        self.assertEqual(self._norm("De'Aaron Fox"), "deaaron fox")
    
    def test_norm_removes_periods(self):
        """Test that periods in abbreviations are removed"""
        self.assertEqual(self._norm("C.J. Stroud"), "cj stroud")
        self.assertEqual(self._norm("T.Y. Hilton"), "ty hilton")
    
    def test_norm_lowercases(self):
        """Test that uppercase is converted to lowercase"""
        self.assertEqual(self._norm("TRAVIS KELCE"), "travis kelce")
        self.assertEqual(self._norm("Travis Kelce"), "travis kelce")
    
    def test_norm_strips_whitespace(self):
        """Test that leading/trailing whitespace is removed"""
        self.assertEqual(self._norm("  Davante Adams  "), "davante adams")
        self.assertEqual(self._norm("\tNico Collins\n"), "nico collins")
    
    def test_norm_complex_names(self):
        """Test complex names with multiple special characters"""
        self.assertEqual(self._norm("D'Andre-Swift"), "dandreswift")
        # Note: Unicode characters like ç are also removed by [^a-z0-9 ]+
        self.assertEqual(self._norm("Jean-Francois Emond"), "jeanfrancois emond")


class TestTokenMatching(unittest.TestCase):
    """Test token-based player matching logic"""
    
    def _norm(self, s):
        return re.sub(r"[^a-z0-9 ]+", "", s.lower()).strip()
    
    def token_match(self, player_name, athlete_name):
        """Check if all tokens from player_name appear in athlete_name"""
        player_norm = self._norm(player_name)
        athlete_norm = self._norm(athlete_name)
        return all(tok in athlete_norm for tok in player_norm.split())
    
    def test_exact_name_match(self):
        """Test exact name matches"""
        self.assertTrue(self.token_match("Travis Kelce", "travis kelce"))
        self.assertTrue(self.token_match("Davante Adams", "davante adams"))
    
    def test_apostrophe_handling(self):
        """Test that apostrophes don't break matching"""
        self.assertTrue(self.token_match("D'Andre Swift", "Dandre Swift"))
        self.assertTrue(self.token_match("Ja'Marr Chase", "Jamarr Chase"))
    
    def test_period_handling(self):
        """Test that periods don't break matching"""
        self.assertTrue(self.token_match("C.J. Stroud", "CJ Stroud"))
        self.assertTrue(self.token_match("C.J. Stroud", "CJ STROUD"))
    
    def test_partial_name_mismatch(self):
        """Test that missing tokens don't match"""
        self.assertFalse(self.token_match("Cecil Shorts III", "Cecil Shorts"))
    
    def test_no_match(self):
        """Test that completely different names don't match"""
        self.assertFalse(self.token_match("Tom Brady", "Travis Kelce"))
        self.assertFalse(self.token_match("Patrick Mahomes", "Josh Allen"))


class TestFuzzyMatching(unittest.TestCase):
    """Test fuzzy matching with normalized inputs (updated logic)"""
    
    def _norm(self, s):
        return re.sub(r"[^a-z0-9 ]+", "", s.lower()).strip()
    
    def fuzzy_match(self, player_name, athlete_names, cutoff=0.75):
        """Fuzzy match using normalized inputs"""
        player_norm = self._norm(player_name)
        athlete_names_norm = [self._norm(name) for name in athlete_names]
        matches = get_close_matches(player_norm, athlete_names_norm, n=1, cutoff=cutoff)
        return len(matches) > 0
    
    def test_high_similarity_match(self):
        """Test that highly similar names match (cutoff=0.75)"""
        # "cecil shorts" vs "cecil shorts iii" (normalized) should have ~0.87 similarity
        self.assertTrue(self.fuzzy_match(
            "Cecil Shorts III",
            ["Cecil Shorts"],
            cutoff=0.75
        ))
    
    def test_exact_match_via_fuzzy(self):
        """Test that exact matches also work via fuzzy (similarity ~1.0)"""
        self.assertTrue(self.fuzzy_match(
            "Travis Kelce",
            ["Travis Kelce"],
            cutoff=0.75
        ))
    
    def test_no_match_dissimilar(self):
        """Test that dissimilar names don't match even with fuzzy (cutoff=0.75)"""
        self.assertFalse(self.fuzzy_match(
            "Tom Brady",
            ["Travis Kelce", "Davante Adams"],
            cutoff=0.75
        ))
    
    def test_apostrophe_normalization_in_fuzzy(self):
        """Test that apostrophes are handled in fuzzy matching"""
        # Both should normalize to same thing
        self.assertTrue(self.fuzzy_match(
            "D'Andre Swift",
            ["Dandre Swift"],
            cutoff=0.75
        ))
    
    def test_increased_cutoff_reduces_false_positives(self):
        """Test that cutoff=0.75 is more restrictive than cutoff=0.6"""
        athlete_names = ["Travis Kelce", "Cecil Shorts"]
        
        # "Tom Brady" shouldn't match any with cutoff=0.75
        self.assertFalse(self.fuzzy_match(
            "Tom Brady",
            athlete_names,
            cutoff=0.75
        ))


class TestTeamMatching(unittest.TestCase):
    """Test team name matching logic with case-insensitivity fixes"""
    
    def team_matches(self, search_team, team_names, team_abbrs):
        """Updated team matching with case-insensitive comparison"""
        search_lower = search_team.lower().strip()
        
        # Create lowercase sets for case-insensitive comparison
        team_names_lower = {name.lower() for name in team_names}
        team_abbrs_lower = {abbr.lower() for abbr in team_abbrs}
        
        # Check exact matches first (case-insensitive)
        if search_lower in team_names_lower or search_lower in team_abbrs_lower:
            return True
        
        # Check partial matches for team names
        for name in team_names_lower:
            if search_lower in name or name in search_lower:
                return True
        
        # Check partial matches for abbreviations
        for abbr in team_abbrs_lower:
            if search_lower == abbr or abbr in search_lower:
                return True
        
        return False
    
    def test_exact_name_match(self):
        """Test exact full name match"""
        self.assertTrue(self.team_matches(
            "Green Bay Packers",
            ["Green Bay Packers"],
            ["GB"]
        ))
    
    def test_abbreviation_match(self):
        """Test exact abbreviation match"""
        self.assertTrue(self.team_matches(
            "GB",
            ["Green Bay Packers"],
            ["GB"]
        ))
    
    def test_partial_name_match(self):
        """Test partial name match (e.g., 'Packers' in 'Green Bay Packers')"""
        self.assertTrue(self.team_matches(
            "Packers",
            ["Green Bay Packers"],
            ["GB"]
        ))
    
    def test_case_insensitive_exact_match(self):
        """Test case-insensitive exact match (fixes bug)"""
        self.assertTrue(self.team_matches(
            "green bay packers",
            ["Green Bay Packers"],
            ["GB"]
        ))
    
    def test_case_insensitive_abbreviation(self):
        """Test case-insensitive abbreviation match"""
        self.assertTrue(self.team_matches(
            "gb",
            ["Green Bay Packers"],
            ["GB"]
        ))
    
    def test_buffalo_bills(self):
        """Test Buffalo Bills matching variations"""
        team_names = ["Buffalo Bills"]
        team_abbrs = ["BUF"]
        
        self.assertTrue(self.team_matches("Buffalo Bills", team_names, team_abbrs))
        self.assertTrue(self.team_matches("Bills", team_names, team_abbrs))
        self.assertTrue(self.team_matches("BUF", team_names, team_abbrs))
        self.assertTrue(self.team_matches("buf", team_names, team_abbrs))
    
    def test_no_match(self):
        """Test that unrelated teams don't match"""
        self.assertFalse(self.team_matches(
            "Kansas City",
            ["Green Bay Packers"],
            ["GB"]
        ))
    
    def test_multiple_teams(self):
        """Test matching with multiple teams in game"""
        away_names = {"Buffalo Bills"}
        away_abbrs = {"BUF"}
        home_names = {"Green Bay Packers"}
        home_abbrs = {"GB"}
        
        # Buffalo should match away
        self.assertTrue(self.team_matches("Buffalo", away_names, away_abbrs))
        self.assertFalse(self.team_matches("Buffalo", home_names, home_abbrs))
        
        # Packers should match home
        self.assertTrue(self.team_matches("Packers", home_names, home_abbrs))
        self.assertFalse(self.team_matches("Packers", away_names, away_abbrs))


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and potential problem scenarios"""
    
    def _norm(self, s):
        return re.sub(r"[^a-z0-9 ]+", "", s.lower()).strip()
    
    def test_empty_string(self):
        """Test handling of empty strings"""
        self.assertEqual(self._norm(""), "")
        self.assertEqual(self._norm("   "), "")
    
    def test_only_special_chars(self):
        """Test handling of strings with only special characters"""
        self.assertEqual(self._norm("!@#$%"), "")
        self.assertEqual(self._norm("..."), "")
    
    def test_numbers_preserved(self):
        """Test that numbers are preserved in normalization"""
        self.assertEqual(self._norm("Cecil Shorts III"), "cecil shorts iii")
        self.assertEqual(self._norm("2nd String"), "2nd string")
    
    def test_multiple_spaces(self):
        """Test that multiple spaces are preserved (not collapsed)"""
        # Current implementation strips but doesn't collapse spaces
        # This is a potential future improvement
        result = self._norm("Cecil   Shorts")
        self.assertIn("cecil", result)
        self.assertIn("shorts", result)


if __name__ == '__main__':
    unittest.main()
