from datetime import datetime
from bson import ObjectId
from app.models import User, Match, Tournament, RecentMatch
from typing import List, Dict, Any
from app.utils.logging import get_logger
from app.utils.auth import user_helper
from itertools import groupby

logger = get_logger(__name__)


def generate_round_robin_matches(player_ids: List[str], tournament_id: str, rounds_per_matchup: int = 2) -> List[dict]:
    """
    Generate round-robin matches for all players in a tournament.
    Each player plays against every other player the specified number of times.
    For even numbered rounds, player positions are alternated (player1 becomes player2 and vice versa).
    
    Args:
        player_ids: List of player IDs in the tournament
        tournament_id: The tournament ID these matches belong to
        rounds_per_matchup: Number of times each pair of players should play against each other
        
    Returns:
        List of match dictionaries ready to be inserted into the database
    """
    matches = []
    
    # Generate all unique pairs of players
    player_pairs = list(itertools.combinations(player_ids, 2))
    
    for round_num in range(rounds_per_matchup):
        for player1_id, player2_id in player_pairs:
            # For even-numbered rounds (1, 3, 5...), reverse the player positions
            if round_num % 2 == 1:
                actual_player1_id = str(player2_id)
                actual_player2_id = str(player1_id)
            else:
                actual_player1_id = str(player1_id)
                actual_player2_id = str(player2_id)
            
            match_dict = {
                "player1_id": actual_player1_id,
                "player2_id": actual_player2_id,
                "player1_goals": 0,
                "player2_goals": 0,
                "tournament_id": str(tournament_id),
                "team1": "",  # Blank as requested
                "team2": "",  # Blank as requested
                "half_length": 4,  # Default value
                "completed": False,  # Not completed initially
                "date": datetime.now()
            }
            matches.append(match_dict)
    
    logger.info(f"Generated {len(matches)} round-robin matches for {len(player_ids)} players with {rounds_per_matchup} rounds per matchup")
    return matches


def generate_missing_matches(existing_matches: List[dict], player_ids: List[str], tournament_id: str, rounds_per_matchup: int = 2) -> List[dict]:
    """
    Generate only the missing matches to complete the round-robin format while preserving existing matches.
    For even numbered rounds, player positions are alternated (player1 becomes player2 and vice versa).
    
    Args:
        existing_matches: List of existing matches in the tournament
        player_ids: Current list of all player IDs in the tournament
        tournament_id: The tournament ID these matches belong to
        rounds_per_matchup: Number of times each pair of players should play against each other
        
    Returns:
        List of new match dictionaries that need to be created
    """
    if len(player_ids) < 2:
        return []
    
    # Track existing matchups and their counts, considering player order
    existing_matchups = {}
    
    for match in existing_matches:
        p1_id = str(match.get("player1_id", ""))
        p2_id = str(match.get("player2_id", ""))
        
        # Only consider matches involving current players
        if p1_id in player_ids and p2_id in player_ids:
            # Create a key that preserves player order (p1_id, p2_id) vs (p2_id, p1_id)
            matchup_key = (p1_id, p2_id)
            existing_matchups[matchup_key] = existing_matchups.get(matchup_key, 0) + 1
    
    # Generate all required matchups
    player_pairs = list(itertools.combinations(player_ids, 2))
    new_matches = []
    
    for player1_id, player2_id in player_pairs:
        # We need to generate matches for both directions if rounds_per_matchup > 1
        for round_num in range(rounds_per_matchup):
            # For even-numbered rounds (1, 3, 5...), reverse the player positions
            if round_num % 2 == 1:
                actual_player1_id = str(player2_id)
                actual_player2_id = str(player1_id)
            else:
                actual_player1_id = str(player1_id)
                actual_player2_id = str(player2_id)
            
            # Check if this specific matchup (with this player order) already exists
            matchup_key = (actual_player1_id, actual_player2_id)
            existing_count = existing_matchups.get(matchup_key, 0)
            
            if existing_count == 0:
                # This specific matchup doesn't exist, create it
                match_dict = {
                    "player1_id": actual_player1_id,
                    "player2_id": actual_player2_id,
                    "player1_goals": 0,
                    "player2_goals": 0,
                    "tournament_id": str(tournament_id),
                    "team1": "",  # Blank as requested
                    "team2": "",  # Blank as requested
                    "half_length": 4,  # Default value
                    "completed": False,  # Not completed initially
                    "date": datetime.now()
                }
                new_matches.append(match_dict)
                
                # Mark this matchup as created to avoid duplicates
                existing_matchups[matchup_key] = 1
    
    logger.info(f"Generated {len(new_matches)} missing matches for {len(player_ids)} players. Preserved {len(existing_matches)} existing matches.")
    return new_matches




async def match_helper(match : Match, db) -> dict:
    """Convert match document to dict format with player names"""
    start_time = time.time()
    match_id = str(match.get("_id", "unknown"))
    logger.info(f"Starting match_helper for match_id: {match_id}")
    
    try:
        # Get player information
        player1_id = match.get("player1_id")
        player2_id = match.get("player2_id")
        
        if not player1_id or not player2_id:
            logger.error(f"Match missing player IDs: {match.get('_id')}")
            error_time = time.time()
            logger.info(f"match_helper completed with error in {(error_time - start_time) * 1000:.2f}ms - match_id: {match_id}")
            return {
                "id": str(match["_id"]),
                "player1_name": "Unknown Player",
                "player2_name": "Unknown Player",
                "player1_goals": match.get("player1_goals", 0),
                "player2_goals": match.get("player2_goals", 0),
                "date": match.get("date", datetime.now()),
                "team1": match.get("team1", "Unknown"),
                "team2": match.get("team2", "Unknown"),
                "half_length": match.get("half_length", 4),  # Default to 4 minutes if not set
            }
        
        # Find players
        players_start = time.time()
        player1 : User = await db.users.find_one({"_id": ObjectId(player1_id)})
        player2 : User = await db.users.find_one({"_id": ObjectId(player2_id)})
        players_time = time.time()
        logger.info(f"Player queries completed in {(players_time - players_start) * 1000:.2f}ms - match_id: {match_id}, player1_id: {player1_id}, player2_id: {player2_id}")
        
        # Handle deleted players
        if player1 and player1.get("is_deleted", False):
            player1_name = "Deleted Player"
        else:
            player1_name = player1["username"] if player1 else "Unknown Player"
            
        if player2 and player2.get("is_deleted", False):
            player2_name = "Deleted Player"
        else:
            player2_name = player2["username"] if player2 else "Unknown Player"
        
        result = {
            "id": str(match["_id"]),
            "player1_name": player1_name,
            "player2_name": player2_name,
            "player1_goals": match.get("player1_goals", 0),
            "player2_goals": match.get("player2_goals", 0),
            "date": match.get("date", datetime.now()),
            "team1": match.get("team1", "Unknown"),
            "team2": match.get("team2", "Unknown"),
            "half_length": match.get("half_length", 4),  # Default to 4 minutes if not set
            "completed": match.get("completed", False),  # Include completed status
        }
        
        # Add tournament info if available
        tournament_start = time.time()
        if match.get("tournament_id"):
            tournament : Tournament = await db.tournaments.find_one({"_id": ObjectId(match["tournament_id"])})
            if tournament:
                result["tournament_name"] = tournament["name"]
        tournament_time = time.time()
        if match.get("tournament_id"):
            logger.info(f"Tournament query completed in {(tournament_time - tournament_start) * 1000:.2f}ms - match_id: {match_id}, tournament_id: {match['tournament_id']}")
        
        total_time = time.time()
        logger.info(f"match_helper completed successfully in {(total_time - start_time) * 1000:.2f}ms - match_id: {match_id}, player1: {player1_name}, player2: {player2_name}")
        
        return result
    except Exception as e:
        error_time = time.time()
        logger.error(f"Error in match_helper: {str(e)} - match_id: {match_id}")
        logger.info(f"match_helper failed with exception in {(error_time - start_time) * 1000:.2f}ms - match_id: {match_id}")
        # Return a minimal valid response
        return {
            "id": str(match.get("_id", "unknown")),
            "player1_name": "Error",
            "player2_name": "Error",
            "player1_goals": 0,
            "player2_goals": 0,
            "date": datetime.now(),
            "half_length": match.get("half_length", 4),  # Default to 4 minutes if not set
        }


def get_result(player1_goals, player2_goals, is_player1):
    """Calculate win/loss/draw result for a player"""
    if is_player1:
        if player1_goals > player2_goals:
            return {"win": 1, "loss": 0, "draw": 0}
        elif player1_goals < player2_goals:
            return {"win": 0, "loss": 1, "draw": 0}
        else:
            return {"win": 0, "loss": 0, "draw": 1}
    else:
        if player2_goals > player1_goals:
            return {"win": 1, "loss": 0, "draw": 0}
        elif player2_goals < player1_goals:
            return {"win": 0, "loss": 1, "draw": 0}
        else:
            return {"win": 0, "loss": 0, "draw": 1}


def calculate_tournament_stats(player_id: str, matches: List[dict]) -> dict:
    """Calculate tournament statistics for a specific player based on match data"""
    stats = {
        "total_matches": 0,
        "total_goals_scored": 0,
        "total_goals_conceded": 0,
        "wins": 0,
        "losses": 0,
        "draws": 0,
        "points": 0
    }
    
    for match in matches:
        player1_id = match.get("player1_id")
        player2_id = match.get("player2_id")
        player1_goals = match.get("player1_goals", 0)
        player2_goals = match.get("player2_goals", 0)
        
        # Convert ObjectIds to strings for comparison
        player1_id_str = str(player1_id) if player1_id else None
        player2_id_str = str(player2_id) if player2_id else None
        
        # Skip matches where this player is not involved
        if player_id not in [player1_id_str, player2_id_str]:
            continue
            
        stats["total_matches"] += 1
        
        # Determine if this player is player1 or player2
        is_player1 = player_id == player1_id_str
        
        if is_player1:
            stats["total_goals_scored"] += player1_goals
            stats["total_goals_conceded"] += player2_goals
            result = get_result(player1_goals, player2_goals, True)
        else:
            stats["total_goals_scored"] += player2_goals
            stats["total_goals_conceded"] += player1_goals
            result = get_result(player1_goals, player2_goals, False)
        
        stats["wins"] += result["win"]
        stats["losses"] += result["loss"]
        stats["draws"] += result["draw"]
        
        # Calculate points (3 for win, 1 for draw, 0 for loss)
        stats["points"] += (result["win"] * 3) + (result["draw"] * 1)
    
    # Calculate goal difference
    stats["goal_difference"] = stats["total_goals_scored"] - stats["total_goals_conceded"]
    
    return stats


async def calculate_head_to_head_stats(db, player1_id: str, player2_id: str, player1: dict, player2: dict) -> dict:
    """
    Calculate head-to-head statistics between two players.
    
    Args:
        db: Database connection
        player1_id: ID of the first player
        player2_id: ID of the second player  
        player1: User 1 document from database
        player2: User 2 document from database
        
    Returns:
        Dictionary containing head-to-head statistics
    """
    # Find all matches between these two players
    matches = await db.matches.find({
        "$or": [
            {"player1_id": player1_id, "player2_id": player2_id},
            {"player1_id": player2_id, "player2_id": player1_id}
        ]
    }).sort("date", -1).to_list(1000)
    
    # Initialize stats
    stats = {
        "player1_id": player1_id,
        "player2_id": player2_id,
        "player1_name": player1.get("username", "Unknown Player"),
        "player2_name": player2.get("username", "Unknown Player"),
        "total_matches": 0,
        "player1_wins": 0,
        "player2_wins": 0,
        "draws": 0,
        "player1_goals": 0,
        "player2_goals": 0,
        "player1_win_rate": 0.0,
        "player2_win_rate": 0.0,
        "player1_avg_goals": 0.0,
        "player2_avg_goals": 0.0,
        "recent_matches": []
    }
    
    # Process each match
    for match in matches:
        stats["total_matches"] += 1
        
        # Determine which player is player1 in this match
        is_player1_first = match["player1_id"] == player1_id
        
        if is_player1_first:
            p1_goals = match["player1_goals"]
            p2_goals = match["player2_goals"]
        else:
            p1_goals = match["player2_goals"]
            p2_goals = match["player1_goals"]
        
        # Add goals
        stats["player1_goals"] += p1_goals
        stats["player2_goals"] += p2_goals
        
        # Determine result
        if p1_goals > p2_goals:
            stats["player1_wins"] += 1
        elif p1_goals < p2_goals:
            stats["player2_wins"] += 1
        else:
            stats["draws"] += 1
    
    # Calculate derived statistics
    if stats["total_matches"] > 0:
        stats["player1_win_rate"] = round(stats["player1_wins"] / stats["total_matches"], 3)
        stats["player2_win_rate"] = round(stats["player2_wins"] / stats["total_matches"], 3)
        stats["player1_avg_goals"] = round(stats["player1_goals"] / stats["total_matches"], 2)
        stats["player2_avg_goals"] = round(stats["player2_goals"] / stats["total_matches"], 2)
    
    # Get recent matches (last 5)
    recent_matches = []
    for match in matches[:5]:  # Get last 5 matches
        # Determine which player is player1 in this match
        is_player1_first = match["player1_id"] == player1_id
        
        if is_player1_first:
            p1_goals = match["player1_goals"]
            p2_goals = match["player2_goals"]
        else:
            p1_goals = match["player2_goals"]
            p2_goals = match["player1_goals"]
        
        # Get tournament info if available
        tournament_name = None
        if match.get("tournament_id"):
            tournament = await db.tournaments.find_one({"_id": ObjectId(match["tournament_id"])})
            if tournament:
                tournament_name = tournament.get("name")
        
        recent_match = {
            "date": match.get("date"),
            "player1_goals": p1_goals,
            "player2_goals": p2_goals,
            "tournament_name": tournament_name,
            "team1": match.get("team1"),
            "team2": match.get("team2")
        }
        recent_matches.append(recent_match)
    
    stats["recent_matches"] = recent_matches
    
    return stats


async def calculate_user_detailed_stats(user_id: str, db) -> Dict[str, Any]:
    """
    Calculate detailed statistics for a user.
    This function performs all the expensive calculations for user detailed stats.
    
    Args:
        user_id: The ID of the user to calculate stats for
        db: Database connection
        
    Returns:
        Dictionary containing all the detailed stats matching UserDetailedStats model
    """
    # Get user
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise ValueError(f"User not found: {user_id}")
    
    # Get all matches for this user
    matches = await db.matches.find({
        "$or": [
            {"player1_id": user_id},
            {"player2_id": user_id}
        ]
    }).sort("date", 1).to_list(1000)
    
    # Calculate wins/losses against each opponent
    wins_against = {}
    losses_against = {}
    
    for match in matches:
        opponent_id = (
            match["player2_id"]
            if match["player1_id"] == user_id
            else match["player1_id"]
        )
        opponent = await db.users.find_one({"_id": ObjectId(opponent_id)})
        
        if not opponent:
            continue
        
        if match["player1_id"] == user_id:
            if match["player1_goals"] > match["player2_goals"]:
                wins_against[opponent["username"]] = (
                    wins_against.get(opponent["username"], 0) + 1
                )
            elif match["player1_goals"] < match["player2_goals"]:
                losses_against[opponent["username"]] = (
                    losses_against.get(opponent["username"], 0) + 1
                )
        else:
            if match["player2_goals"] > match["player1_goals"]:
                wins_against[opponent["username"]] = (
                    wins_against.get(opponent["username"], 0) + 1
                )
            elif match["player2_goals"] < match["player1_goals"]:
                losses_against[opponent["username"]] = (
                    losses_against.get(opponent["username"], 0) + 1
                )
    
    highest_wins = (
        max(wins_against.items(), key=lambda x: x[1]) if wins_against else None
    )
    highest_losses = (
        max(losses_against.items(), key=lambda x: x[1]) if losses_against else None
    )
    
    # Calculate winrate over time (per day)
    total_matches = 0
    total_wins = 0
    daily_winrate = []
    
    # Convert match dates to datetime objects if they're strings
    for match in matches:
        if isinstance(match["date"], str):
            match["date"] = datetime.fromisoformat(match["date"])
    
    # Group matches by date
    for date, day_matches in groupby(matches, key=lambda x: x["date"].date()):
        day_matches = list(day_matches)
        for match in day_matches:
            total_matches += 1
            is_player1 = match["player1_id"] == user_id
            player_goals = (
                match["player1_goals"] if is_player1 else match["player2_goals"]
            )
            opponent_goals = (
                match["player2_goals"] if is_player1 else match["player1_goals"]
            )
            
            if player_goals > opponent_goals:
                total_wins += 1
        
        winrate = total_wins / total_matches if total_matches > 0 else 0
        # Convert date to datetime at midnight
        date_dt = datetime.combine(date, datetime.min.time())
        daily_winrate.append({"date": date_dt, "winrate": winrate})
    
    # Calculate tournament participation
    tournaments = await db.tournaments.find({
        "player_ids": {"$in": [user_id]}
    }).to_list(1000)
    
    tournaments_played = len(tournaments)
    tournament_ids = [str(t["_id"]) for t in tournaments]
    
    # Build stats dictionary
    stats = user_helper(user)
    stats.update({
        "win_rate": (
            user["wins"] / user["total_matches"]
            if user["total_matches"] > 0
            else 0
        ),
        "average_goals_scored": (
            user["total_goals_scored"] / user["total_matches"]
            if user["total_matches"] > 0
            else 0
        ),
        "average_goals_conceded": (
            user["total_goals_conceded"] / user["total_matches"]
            if user["total_matches"] > 0
            else 0
        ),
        "highest_wins_against": (
            {highest_wins[0]: highest_wins[1]} if highest_wins else None
        ),
        "highest_losses_against": (
            {highest_losses[0]: highest_losses[1]} if highest_losses else None
        ),
        "winrate_over_time": daily_winrate,
        "tournaments_played": tournaments_played,
        "tournament_ids": tournament_ids,
    })
    
    # Get user's last 5 completed matches
    user_matches = await db.matches.find({
        "$or": [
            {"player1_id": user_id},
            {"player2_id": user_id}
        ],
        "completed": True
    }).sort("date", -1).limit(5).to_list(5)
    
    # Convert matches to RecentMatch format
    recent_matches = []
    for match in user_matches:
        # Get tournament name if available
        tournament_name = None
        if match.get("tournament_id"):
            tournament = await db.tournaments.find_one({"_id": ObjectId(match["tournament_id"])})
            if tournament:
                tournament_name = tournament.get("name")
        
        # Get opponent information
        opponent_id = match["player2_id"] if match["player1_id"] == user_id else match["player1_id"]
        opponent = await db.users.find_one({"_id": ObjectId(opponent_id)})
        
        # Determine current user's goals and opponent's goals
        current_user_goals = match["player1_goals"] if match["player1_id"] == user_id else match["player2_goals"]
        opponent_goals = match["player2_goals"] if match["player1_id"] == user_id else match["player1_goals"]
        
        # Determine match result from current user's perspective
        if current_user_goals > opponent_goals:
            match_result = "win"
        elif current_user_goals < opponent_goals:
            match_result = "loss"
        else:
            match_result = "draw"
        
        recent_match = RecentMatch(
            date=match["date"],
            player1_goals=match["player1_goals"],
            player2_goals=match["player2_goals"],
            tournament_name=tournament_name,
            team1=match.get("team1"),
            team2=match.get("team2"),
            opponent_id=opponent_id,
            opponent_username=opponent.get("username") if opponent else None,
            opponent_first_name=opponent.get("first_name") if opponent else None,
            opponent_last_name=opponent.get("last_name") if opponent else None,
            current_player_id=user_id,
            current_player_username=user.get("username"),
            current_player_goals=current_user_goals,
            opponent_goals=opponent_goals,
            match_result=match_result
        )
        recent_matches.append(recent_match)
    
    # Add last_5_matches to stats
    stats["last_5_matches"] = recent_matches
    
    return stats


async def update_user_detailed_stats_cache(user_id: str, db) -> None:
    """
    Update the detailed stats cache for a user.
    This function calculates and stores the cache in the database.
    
    Args:
        user_id: The ID of the user to update cache for
        db: Database connection
    """
    try:
        stats = await calculate_user_detailed_stats(user_id, db)
        
        # Convert RecentMatch objects to dicts for storage
        stats_for_cache = stats.copy()
        if "last_5_matches" in stats_for_cache and stats_for_cache["last_5_matches"]:
            stats_for_cache["last_5_matches"] = [
                match.model_dump() if hasattr(match, "model_dump") 
                else match.dict() if hasattr(match, "dict")
                else dict(match) if hasattr(match, "__dict__")
                else match
                for match in stats["last_5_matches"]
            ]
        
        # Store in cache
        await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    "detailed_stats_cache": stats_for_cache,
                    "cache_updated_at": datetime.utcnow()
                }
            }
        )
    except (ValueError, Exception) as e:
        # Log error but don't raise - cache update shouldn't break match operations
        logger.error(f"Failed to update cache for user {user_id}: {str(e)}")
