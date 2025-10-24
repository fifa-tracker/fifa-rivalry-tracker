#!/usr/bin/env python3
"""
User Statistics Recalculation and Validation Script

This script validates user statistics by:
1. Recalculating stats from match history chronologically
2. Comparing calculated values against current database values
3. Generating detailed reports of discrepancies

Usage:
    python scripts/recalculate_stats.py [--detailed] [--user-id USER_ID]

Options:
    --detailed    Show detailed output for all users
    --user-id     Validate only specific user ID
    --help        Show this help message

Note: This script does NOT update the database - it only validates and reports.
"""

import os
import sys
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict
import asyncio

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from bson import ObjectId
from app.config import settings
from app.api.dependencies import get_database
from app.utils.logging import get_logger
from app.utils.elo import calculate_elo_ratings

logger = get_logger(__name__)


class UserStatsValidator:
    """Validates user statistics by recalculating from match history"""
    
    def __init__(self):
        self.db = None
        self.users = {}
        self.matches = []
        self.validation_results = {}
        
    async def initialize(self):
        """Initialize database connection and load data"""
        try:
            self.db = await get_database()
            logger.info("Database connection established")
            
            # Load all users
            await self.load_users()
            
            # Load all matches sorted by date
            await self.load_matches()
            
            logger.info(f"Loaded {len(self.users)} users and {len(self.matches)} matches")
            
        except Exception as e:
            logger.error(f"Error initializing validator: {str(e)}")
            raise
    
    async def load_users(self):
        """Load all users from database"""
        try:
            cursor = self.db.users.find({})
            users_list = await cursor.to_list(length=None)
            
            self.users = {str(user["_id"]): user for user in users_list}
            logger.info(f"Loaded {len(self.users)} users")
            
        except Exception as e:
            logger.error(f"Error loading users: {str(e)}")
            raise
    
    async def load_matches(self):
        """Load all matches sorted by date"""
        try:
            cursor = self.db.matches.find({}).sort("date", 1)  # Sort by date ascending
            self.matches = await cursor.to_list(length=None)
            logger.info(f"Loaded {len(self.matches)} matches")
            
        except Exception as e:
            logger.error(f"Error loading matches: {str(e)}")
            raise
    
    def calculate_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Calculate expected stats for a user from match history"""
        if user_id not in self.users:
            return None
        
        # Initialize stats
        stats = {
            "total_matches": 0,
            "wins": 0,
            "losses": 0,
            "draws": 0,
            "total_goals_scored": 0,
            "total_goals_conceded": 0,
            "goal_difference": 0,
            "points": 0,
            "elo_rating": settings.DEFAULT_ELO_RATING,
            "last_5_teams": []
        }
        
        # Track teams for last_5_teams calculation
        teams_played = []
        
        # Process matches chronologically
        for match in self.matches:
            player1_id = str(match.get("player1_id", ""))
            player2_id = str(match.get("player2_id", ""))
            
            # Skip if user is not in this match
            if user_id not in [player1_id, player2_id]:
                continue
            
            # Determine if user is player1 or player2
            is_player1 = user_id == player1_id
            
            # Get goals for this user
            if is_player1:
                goals_scored = match.get("player1_goals", 0)
                goals_conceded = match.get("player2_goals", 0)
                team_played = match.get("team1", "")
            else:
                goals_scored = match.get("player2_goals", 0)
                goals_conceded = match.get("player1_goals", 0)
                team_played = match.get("team2", "")
            
            # Update stats
            stats["total_matches"] += 1
            stats["total_goals_scored"] += goals_scored
            stats["total_goals_conceded"] += goals_conceded
            stats["goal_difference"] = stats["total_goals_scored"] - stats["total_goals_conceded"]
            
            # Determine match result
            if goals_scored > goals_conceded:
                stats["wins"] += 1
                stats["points"] += 3
            elif goals_scored < goals_conceded:
                stats["losses"] += 1
                stats["points"] += 0
            else:
                stats["draws"] += 1
                stats["points"] += 1
            
            # Update ELO rating
            if is_player1:
                opponent_rating = self.get_opponent_rating(match, player2_id)
                stats["elo_rating"], _ = calculate_elo_ratings(
                    stats["elo_rating"], opponent_rating, goals_scored, goals_conceded
                )
            else:
                opponent_rating = self.get_opponent_rating(match, player1_id)
                stats["elo_rating"], _ = calculate_elo_ratings(
                    stats["elo_rating"], opponent_rating, goals_scored, goals_conceded
                )
            
            # Track teams for last_5_teams
            if team_played and team_played not in teams_played:
                teams_played.append(team_played)
        
        # Keep only last 5 unique teams
        stats["last_5_teams"] = teams_played[-5:] if len(teams_played) > 5 else teams_played
        
        return stats
    
    def get_opponent_rating(self, match: Dict, opponent_id: str) -> int:
        """Get opponent's ELO rating at the time of the match"""
        # For simplicity, we'll use the current ELO rating
        # In a more sophisticated implementation, we'd track ELO progression
        opponent = self.users.get(opponent_id)
        if opponent:
            return opponent.get("elo_rating", settings.DEFAULT_ELO_RATING)
        return settings.DEFAULT_ELO_RATING
    
    def compare_stats(self, calculated: Dict[str, Any], actual: Dict[str, Any]) -> Dict[str, Any]:
        """Compare calculated stats with actual database values"""
        discrepancies = {}
        
        fields_to_compare = [
            "total_matches", "wins", "losses", "draws",
            "total_goals_scored", "total_goals_conceded", "goal_difference",
            "points", "elo_rating"
        ]
        
        for field in fields_to_compare:
            calculated_val = calculated.get(field, 0)
            actual_val = actual.get(field, 0)
            
            if calculated_val != actual_val:
                discrepancies[field] = {
                    "expected": calculated_val,
                    "actual": actual_val,
                    "difference": calculated_val - actual_val
                }
        
        # Compare last_5_teams (order matters)
        calculated_teams = calculated.get("last_5_teams", [])
        actual_teams = actual.get("last_5_teams", [])
        
        if calculated_teams != actual_teams:
            discrepancies["last_5_teams"] = {
                "expected": calculated_teams,
                "actual": actual_teams,
                "difference": "Different team lists"
            }
        
        return discrepancies
    
    async def validate_user(self, user_id: str) -> Dict[str, Any]:
        """Validate a single user's statistics"""
        if user_id not in self.users:
            return {"error": f"User {user_id} not found"}
        
        user = self.users[user_id]
        calculated_stats = self.calculate_user_stats(user_id)
        
        if not calculated_stats:
            return {"error": f"Could not calculate stats for user {user_id}"}
        
        discrepancies = self.compare_stats(calculated_stats, user)
        
        return {
            "user_id": user_id,
            "username": user.get("username", "Unknown"),
            "calculated_stats": calculated_stats,
            "actual_stats": user,
            "discrepancies": discrepancies,
            "has_discrepancies": len(discrepancies) > 0
        }
    
    async def validate_all_users(self) -> Dict[str, Any]:
        """Validate all users' statistics"""
        results = {}
        users_with_discrepancies = 0
        
        logger.info("Starting validation of all users...")
        
        for user_id in self.users.keys():
            result = await self.validate_user(user_id)
            results[user_id] = result
            
            if result.get("has_discrepancies", False):
                users_with_discrepancies += 1
        
        logger.info(f"Validation completed: {users_with_discrepancies}/{len(self.users)} users have discrepancies")
        
        return {
            "total_users": len(self.users),
            "users_with_discrepancies": users_with_discrepancies,
            "results": results
        }
    
    def print_validation_report(self, validation_results: Dict[str, Any], detailed: bool = False, user_id: Optional[str] = None):
        """Print validation report"""
        print("\n" + "="*60)
        print("USER STATISTICS VALIDATION REPORT")
        print("="*60)
        
        if user_id:
            # Single user report
            if user_id in validation_results["results"]:
                result = validation_results["results"][user_id]
                self.print_user_result(result, detailed=True)
            else:
                print(f"❌ User {user_id} not found in validation results")
        else:
            # Summary report
            total_users = validation_results["total_users"]
            users_with_discrepancies = validation_results["users_with_discrepancies"]
            
            print(f"📊 Total users validated: {total_users}")
            print(f"✅ Users with matching stats: {total_users - users_with_discrepancies}")
            print(f"❌ Users with discrepancies: {users_with_discrepancies}")
            
            if users_with_discrepancies > 0:
                print(f"\n🔍 Users with discrepancies:")
                for uid, result in validation_results["results"].items():
                    if result.get("has_discrepancies", False):
                        self.print_user_result(result, detailed=detailed)
            
            if detailed:
                print(f"\n📋 All users:")
                for uid, result in validation_results["results"].items():
                    self.print_user_result(result, detailed=False)
    
    def print_user_result(self, result: Dict[str, Any], detailed: bool = False):
        """Print result for a single user"""
        username = result.get("username", "Unknown")
        user_id = result.get("user_id", "Unknown")
        has_discrepancies = result.get("has_discrepancies", False)
        
        if has_discrepancies:
            print(f"\n❌ {username} (ID: {user_id}): Discrepancies found")
            discrepancies = result.get("discrepancies", {})
            
            for field, diff in discrepancies.items():
                if field == "last_5_teams":
                    print(f"  - {field}: Expected {diff['expected']}, Found {diff['actual']}")
                else:
                    expected = diff["expected"]
                    actual = diff["actual"]
                    difference = diff["difference"]
                    sign = "+" if difference > 0 else ""
                    print(f"  - {field}: Expected {expected}, Found {actual} (diff: {sign}{difference})")
        else:
            if detailed:
                print(f"\n✅ {username} (ID: {user_id}): All stats match")
            else:
                print(f"✅ {username}: All stats match")


async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Validate user statistics by recalculating from match history")
    parser.add_argument("--detailed", action="store_true", help="Show detailed output for all users")
    parser.add_argument("--user-id", type=str, help="Validate only specific user ID")
    
    args = parser.parse_args()
    
    try:
        validator = UserStatsValidator()
        await validator.initialize()
        
        if args.user_id:
            # Validate single user
            logger.info(f"Validating user: {args.user_id}")
            result = await validator.validate_user(args.user_id)
            validation_results = {
                "total_users": 1,
                "users_with_discrepancies": 1 if result.get("has_discrepancies", False) else 0,
                "results": {args.user_id: result}
            }
            validator.print_validation_report(validation_results, detailed=True, user_id=args.user_id)
        else:
            # Validate all users
            logger.info("Validating all users...")
            validation_results = await validator.validate_all_users()
            validator.print_validation_report(validation_results, detailed=args.detailed)
        
        print(f"\n📝 Note: This script only validates statistics - it does not update the database.")
        print(f"🕒 Validation completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except KeyboardInterrupt:
        logger.info("Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Validation failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
