#!/usr/bin/env python3
"""
Simple test script to verify the helper functions for tournament match generation
"""

import sys
import os
sys.path.append('/home/roshan/fifa-rivalry-tracker')

from app.utils.helpers import generate_round_robin_matches, generate_missing_matches
from datetime import datetime

def test_generate_round_robin_matches():
    """Test the round-robin match generation"""
    print("Testing generate_round_robin_matches...")
    
    # Test with 3 players, 2 rounds per matchup
    player_ids = ["player1", "player2", "player3"]
    tournament_id = "tournament123"
    rounds_per_matchup = 2
    
    matches = generate_round_robin_matches(player_ids, tournament_id, rounds_per_matchup)
    
    print(f"Generated {len(matches)} matches for {len(player_ids)} players with {rounds_per_matchup} rounds")
    
    # Should be 3 pairs (p1-p2, p1-p3, p2-p3) * 2 rounds = 6 matches
    expected_matches = 6
    assert len(matches) == expected_matches, f"Expected {expected_matches} matches, got {len(matches)}"
    
    # Check that all matches have the required fields
    for match in matches:
        assert "player1_id" in match
        assert "player2_id" in match
        assert "tournament_id" in match
        assert match["tournament_id"] == tournament_id
        assert match["completed"] is False
        assert match["team1"] == ""
        assert match["team2"] == ""
        assert match["player1_goals"] == 0
        assert match["player2_goals"] == 0
    
    print("✓ generate_round_robin_matches test passed!")

def test_generate_missing_matches():
    """Test the missing match generation"""
    print("\nTesting generate_missing_matches...")
    
    # Setup: existing matches for players 1 and 2 (1 round each)
    existing_matches = [
        {
            "_id": "match1",
            "player1_id": "player1",
            "player2_id": "player2",
            "tournament_id": "tournament123",
            "completed": False
        }
    ]
    
    # Now we have 3 players total, and want 2 rounds per matchup
    current_player_ids = ["player1", "player2", "player3"]
    tournament_id = "tournament123"
    rounds_per_matchup = 2
    
    missing_matches = generate_missing_matches(
        existing_matches, 
        current_player_ids, 
        tournament_id, 
        rounds_per_matchup
    )
    
    print(f"Generated {len(missing_matches)} missing matches")
    
    # Should generate:
    # - 1 more match for player1-player2 (to complete 2 rounds)
    # - 2 matches for player1-player3 (new pair, 2 rounds)
    # - 2 matches for player2-player3 (new pair, 2 rounds)
    # Total: 5 missing matches
    expected_missing = 5
    assert len(missing_matches) == expected_missing, f"Expected {expected_missing} missing matches, got {len(missing_matches)}"
    
    # Check that all missing matches have the required fields
    for match in missing_matches:
        assert "player1_id" in match
        assert "player2_id" in match
        assert "tournament_id" in match
        assert match["tournament_id"] == tournament_id
        assert match["completed"] is False
        assert match["team1"] == ""
        assert match["team2"] == ""
    
    print("✓ generate_missing_matches test passed!")

def test_missing_matches_with_completed():
    """Test that completed matches are preserved"""
    print("\nTesting generate_missing_matches with completed matches...")
    
    # Setup: some completed and some incomplete matches
    existing_matches = [
        {
            "_id": "match1",
            "player1_id": "player1",
            "player2_id": "player2",
            "tournament_id": "tournament123",
            "completed": True,  # This one is completed
            "player1_goals": 2,
            "player2_goals": 1
        },
        {
            "_id": "match2",
            "player1_id": "player1",
            "player2_id": "player2",
            "tournament_id": "tournament123",
            "completed": False  # This one is not completed
        }
    ]
    
    # Add a new player
    current_player_ids = ["player1", "player2", "player3"]
    tournament_id = "tournament123"
    rounds_per_matchup = 2
    
    missing_matches = generate_missing_matches(
        existing_matches, 
        current_player_ids, 
        tournament_id, 
        rounds_per_matchup
    )
    
    print(f"Generated {len(missing_matches)} missing matches")
    
    # Should generate:
    # - 0 more matches for player1-player2 (already have 2 rounds)
    # - 2 matches for player1-player3 (new pair, 2 rounds)
    # - 2 matches for player2-player3 (new pair, 2 rounds)
    # Total: 4 missing matches
    expected_missing = 4
    assert len(missing_matches) == expected_missing, f"Expected {expected_missing} missing matches, got {len(missing_matches)}"
    
    print("✓ generate_missing_matches with completed matches test passed!")

if __name__ == "__main__":
    test_generate_round_robin_matches()
    test_generate_missing_matches()
    test_missing_matches_with_completed()
    print("\n🎉 All helper function tests passed!")
