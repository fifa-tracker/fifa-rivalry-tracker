#!/usr/bin/env python3
"""
Test script to verify player position alternation in round-robin matches
"""

import sys
import os
sys.path.append('/home/roshan/fifa-rivalry-tracker')

from app.utils.helpers import generate_round_robin_matches, generate_missing_matches
from datetime import datetime

def test_player_position_alternation():
    """Test that player positions are alternated in round-robin matches"""
    print("Testing player position alternation...")
    
    # Test with 3 players, 2 rounds per matchup
    player_ids = ["player1", "player2", "player3"]
    tournament_id = "tournament123"
    rounds_per_matchup = 2
    
    matches = generate_round_robin_matches(player_ids, tournament_id, rounds_per_matchup)
    
    print(f"Generated {len(matches)} matches:")
    
    # Group matches by player pairs to verify alternation
    pair_matches = {}
    for match in matches:
        p1 = match["player1_id"]
        p2 = match["player2_id"]
        pair_key = tuple(sorted([p1, p2]))  # Normalize pair for grouping
        
        if pair_key not in pair_matches:
            pair_matches[pair_key] = []
        pair_matches[pair_key].append((p1, p2))
    
    # Verify each pair has alternated positions
    for pair_key, match_list in pair_matches.items():
        print(f"\nPair {pair_key}:")
        for i, (p1, p2) in enumerate(match_list):
            print(f"  Match {i+1}: {p1} vs {p2}")
        
        # For 2 rounds, should have alternated positions
        if len(match_list) == 2:
            first_match = match_list[0]
            second_match = match_list[1]
            
            # Second match should have reversed positions
            assert first_match[0] == second_match[1], f"Expected player positions to be reversed for pair {pair_key}"
            assert first_match[1] == second_match[0], f"Expected player positions to be reversed for pair {pair_key}"
            print(f"  ✓ Player positions correctly alternated for {pair_key}")
    
    print("\n✓ Player position alternation test passed!")

def test_missing_matches_with_alternation():
    """Test missing match generation preserves alternation pattern"""
    print("\nTesting missing matches with alternation...")
    
    # Start with existing matches for player1 vs player2 (first round only)
    existing_matches = [
        {
            "_id": "match1",
            "player1_id": "player1",
            "player2_id": "player2",
            "tournament_id": "tournament123",
            "completed": False
        }
    ]
    
    # Add player3 and generate missing matches
    current_player_ids = ["player1", "player2", "player3"]
    tournament_id = "tournament123"
    rounds_per_matchup = 2
    
    missing_matches = generate_missing_matches(
        existing_matches, 
        current_player_ids, 
        tournament_id, 
        rounds_per_matchup
    )
    
    print(f"Generated {len(missing_matches)} missing matches:")
    
    # Group by pairs to analyze
    pair_matches = {}
    for match in missing_matches:
        p1 = match["player1_id"]
        p2 = match["player2_id"]
        pair_key = tuple(sorted([p1, p2]))
        
        if pair_key not in pair_matches:
            pair_matches[pair_key] = []
        pair_matches[pair_key].append((p1, p2))
    
    for pair_key, match_list in pair_matches.items():
        print(f"\nPair {pair_key}:")
        for i, (p1, p2) in enumerate(match_list):
            print(f"  Missing match {i+1}: {p1} vs {p2}")
    
    # Should generate:
    # - 1 match for player1-player2 (second round with reversed positions: player2 vs player1)
    # - 2 matches for player1-player3 (both rounds with alternation)
    # - 2 matches for player2-player3 (both rounds with alternation)
    assert len(missing_matches) == 5
    
    # Check that we have the reversed match for player1-player2
    player1_player2_matches = [m for m in missing_matches 
                              if set([m["player1_id"], m["player2_id"]]) == set(["player1", "player2"])]
    assert len(player1_player2_matches) == 1
    # The missing match should have player2 as player1 (reversed from existing)
    assert player1_player2_matches[0]["player1_id"] == "player2"
    assert player1_player2_matches[0]["player2_id"] == "player1"
    
    print("\n✓ Missing matches with alternation test passed!")

def test_odd_rounds_per_matchup():
    """Test alternation with odd number of rounds"""
    print("\nTesting with 3 rounds per matchup...")
    
    player_ids = ["player1", "player2"]
    tournament_id = "tournament123"
    rounds_per_matchup = 3
    
    matches = generate_round_robin_matches(player_ids, tournament_id, rounds_per_matchup)
    
    print(f"Generated {len(matches)} matches for 3 rounds:")
    for i, match in enumerate(matches):
        print(f"  Match {i+1}: {match['player1_id']} vs {match['player2_id']}")
    
    # Should have 3 matches with alternating pattern:
    # Round 0 (even): player1 vs player2
    # Round 1 (odd):  player2 vs player1  
    # Round 2 (even): player1 vs player2
    assert len(matches) == 3
    assert matches[0]["player1_id"] == "player1" and matches[0]["player2_id"] == "player2"
    assert matches[1]["player1_id"] == "player2" and matches[1]["player2_id"] == "player1"
    assert matches[2]["player1_id"] == "player1" and matches[2]["player2_id"] == "player2"
    
    print("✓ Odd rounds per matchup test passed!")

if __name__ == "__main__":
    test_player_position_alternation()
    test_missing_matches_with_alternation()
    test_odd_rounds_per_matchup()
    print("\n🎉 All player alternation tests passed!")
