#!/usr/bin/env python3
"""
Integration test for tournament functionality
"""

import sys
import os
sys.path.append('/home/roshan/fifa-rivalry-tracker')

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.utils.helpers import generate_round_robin_matches, generate_missing_matches
from datetime import datetime
from bson import ObjectId

async def test_tournament_integration():
    """Test the tournament and match integration"""
    print("Testing tournament integration...")
    
    # Test data
    tournament_id = "tournament_test_123"
    initial_players = ["player1", "player2"]
    rounds_per_matchup = 2
    
    # 1. Create initial matches for 2 players
    print("\n1. Creating initial matches for 2 players...")
    initial_matches = generate_round_robin_matches(
        initial_players, 
        tournament_id, 
        rounds_per_matchup
    )
    print(f"   Created {len(initial_matches)} initial matches")
    
    # Should be 1 pair * 2 rounds = 2 matches
    assert len(initial_matches) == 2
    
    # 2. Add a third player and generate missing matches
    print("\n2. Adding third player and generating missing matches...")
    current_players = ["player1", "player2", "player3"]
    
    # Simulate some existing matches (representing initial_matches that were saved to DB)
    existing_matches = [
        {
            "_id": ObjectId(),
            "player1_id": "player1",
            "player2_id": "player2",
            "tournament_id": tournament_id,
            "completed": False,
            "player1_goals": 0,
            "player2_goals": 0
        },
        {
            "_id": ObjectId(),
            "player1_id": "player1", 
            "player2_id": "player2",
            "tournament_id": tournament_id,
            "completed": False,
            "player1_goals": 0,
            "player2_goals": 0
        }
    ]
    
    missing_matches = generate_missing_matches(
        existing_matches,
        current_players,
        tournament_id,
        rounds_per_matchup
    )
    
    print(f"   Generated {len(missing_matches)} missing matches")
    
    # Should generate:
    # - 0 more for player1-player2 (already have 2)
    # - 2 for player1-player3 
    # - 2 for player2-player3
    # Total: 4 missing matches
    assert len(missing_matches) == 4
    
    # 3. Simulate removing player2 and see what matches should be kept
    print("\n3. Simulating removal of player2...")
    remaining_players = ["player1", "player3"]
    
    # All existing matches (original 2 + new 4 = 6 total)
    all_matches = existing_matches + [
        {
            "_id": ObjectId(),
            "player1_id": "player1",
            "player2_id": "player3", 
            "tournament_id": tournament_id,
            "completed": False
        },
        {
            "_id": ObjectId(),
            "player1_id": "player1",
            "player2_id": "player3",
            "tournament_id": tournament_id,
            "completed": False
        },
        {
            "_id": ObjectId(),
            "player1_id": "player2",
            "player2_id": "player3",
            "tournament_id": tournament_id,
            "completed": False
        },
        {
            "_id": ObjectId(),
            "player1_id": "player2",
            "player2_id": "player3",
            "tournament_id": tournament_id,
            "completed": False
        }
    ]
    
    # Separate matches that involve player2 vs those that don't
    matches_to_keep = []
    matches_to_remove = []
    
    for match in all_matches:
        match_player1_id = str(match.get("player1_id", ""))
        match_player2_id = str(match.get("player2_id", ""))
        
        # If the match involves the removed player (player2)
        if "player2" in [match_player1_id, match_player2_id]:
            matches_to_remove.append(match)
        else:
            # Keep matches that don't involve the removed player and where both players are still in tournament
            if match_player1_id in remaining_players and match_player2_id in remaining_players:
                matches_to_keep.append(match)
    
    print(f"   Matches to keep: {len(matches_to_keep)}")
    print(f"   Matches to remove: {len(matches_to_remove)}")
    
    # Should keep 2 matches (player1 vs player3, both rounds)
    # Should remove 4 matches (2 player1-player2 + 2 player2-player3)
    assert len(matches_to_keep) == 2
    assert len(matches_to_remove) == 4
    
    # Generate any missing matches for remaining players
    missing_after_removal = generate_missing_matches(
        matches_to_keep,
        remaining_players,
        tournament_id,
        rounds_per_matchup
    )
    
    print(f"   Missing matches after removal: {len(missing_after_removal)}")
    
    # Should be 0 because we already have 2 matches for player1-player3
    assert len(missing_after_removal) == 0
    
    print("\n✓ Tournament integration test passed!")

if __name__ == "__main__":
    asyncio.run(test_tournament_integration())
