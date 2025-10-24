#!/usr/bin/env python3
"""
User Statistics Manager Script

This unified script can both validate and update user statistics by:
1. Recalculating stats from match history chronologically
2. Comparing calculated values against current database values
3. Optionally updating the database with correct values
4. Generating detailed reports of discrepancies and changes

Usage:
    python scripts/user_stats_manager.py [OPTIONS]

Options:
    --validate-only    Only validate statistics without updating (default behavior)
    --update          Update database with correct statistics
    --dry-run         Show what would be updated without making changes (requires --update)
    --detailed        Show detailed output for all users
    --user-id USER_ID Validate/update only specific user ID
    --help            Show this help message

Examples:
    # Validate all users (read-only)
    python scripts/user_stats_manager.py --validate-only
    
    # Validate specific user
    python scripts/user_stats_manager.py --validate-only --user-id 507f1f77bcf86cd799439011
    
    # Dry run - see what would be updated
    python scripts/user_stats_manager.py --update --dry-run
    
    # Actually update all users
    python scripts/user_stats_manager.py --update
    
    # Update specific user
    python scripts/user_stats_manager.py --update --user-id 507f1f77bcf86cd799439011

WARNING: Using --update will modify the database. Make sure you have a backup!
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


class UserStatsManager:
    """Unified manager for validating and updating user statistics"""
    
    def __init__(self, update_mode: bool = False, dry_run: bool = False):
        self.db = None
        self.users = {}
        self.matches = []
        self.update_mode = update_mode
        self.dry_run = dry_run
        self.updates_made = 0
        
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
            logger.error(f"Error initializing manager: {str(e)}")
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
    
    async def process_user(self, user_id: str) -> Dict[str, Any]:
        """Process a single user (validate and optionally update)"""
        if user_id not in self.users:
            return {"error": f"User {user_id} not found"}
        
        user = self.users[user_id]
        calculated_stats = self.calculate_user_stats(user_id)
        
        if not calculated_stats:
            return {"error": f"Could not calculate stats for user {user_id}"}
        
        discrepancies = self.compare_stats(calculated_stats, user)
        
        result = {
            "user_id": user_id,
            "username": user.get("username", "Unknown"),
            "calculated_stats": calculated_stats,
            "actual_stats": user,
            "discrepancies": discrepancies,
            "has_discrepancies": len(discrepancies) > 0
        }
        
        # If in update mode and there are discrepancies, handle the update
        if self.update_mode and discrepancies:
            update_result = await self.update_user_stats(user_id, discrepancies)
            result.update(update_result)
        elif self.update_mode and not discrepancies:
            result["status"] = "no_changes_needed"
            result["message"] = "Statistics are already correct"
        else:
            # Validation mode
            result["status"] = "validated"
        
        return result
    
    async def update_user_stats(self, user_id: str, discrepancies: Dict[str, Any]) -> Dict[str, Any]:
        """Update user statistics in the database"""
        # Prepare update data
        update_data = {}
        for field, diff in discrepancies.items():
            if field == "last_5_teams":
                update_data[field] = diff["expected"]
            else:
                update_data[field] = diff["expected"]
        
        if self.dry_run:
            logger.info(f"[DRY RUN] Would update user {self.users[user_id].get('username', 'Unknown')} with: {update_data}")
            return {
                "status": "dry_run",
                "update_data": update_data
            }
        
        # Perform the actual update
        try:
            result = await self.db.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                self.updates_made += 1
                logger.info(f"Updated user {self.users[user_id].get('username', 'Unknown')} with {len(update_data)} fields")
                return {
                    "status": "updated",
                    "update_data": update_data
                }
            else:
                return {
                    "status": "no_changes",
                    "message": "No changes were made to the database"
                }
                
        except Exception as e:
            logger.error(f"Error updating user {user_id}: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def process_all_users(self) -> Dict[str, Any]:
        """Process all users (validate and optionally update)"""
        results = {}
        users_with_discrepancies = 0
        users_updated = 0
        users_with_errors = 0
        
        action = "Updating" if self.update_mode else "Validating"
        logger.info(f"Starting {action.lower()} of all users...")
        
        for user_id in self.users.keys():
            result = await self.process_user(user_id)
            results[user_id] = result
            
            if result.get("has_discrepancies", False):
                users_with_discrepancies += 1
            
            if result.get("status") == "updated":
                users_updated += 1
            elif result.get("status") == "error":
                users_with_errors += 1
        
        if self.update_mode:
            logger.info(f"Update completed: {users_updated} users updated, {users_with_errors} errors")
        else:
            logger.info(f"Validation completed: {users_with_discrepancies}/{len(self.users)} users have discrepancies")
        
        return {
            "total_users": len(self.users),
            "users_with_discrepancies": users_with_discrepancies,
            "users_updated": users_updated,
            "users_with_errors": users_with_errors,
            "updates_made": self.updates_made,
            "results": results
        }
    
    def print_report(self, process_results: Dict[str, Any], detailed: bool = False, user_id: Optional[str] = None):
        """Print processing report"""
        action = "UPDATE" if self.update_mode else "VALIDATION"
        print("\n" + "="*60)
        print(f"USER STATISTICS {action} REPORT")
        print("="*60)
        
        if self.dry_run:
            print("🔍 DRY RUN MODE - No changes were made to the database")
        
        if user_id:
            # Single user report
            if user_id in process_results["results"]:
                result = process_results["results"][user_id]
                self.print_user_result(result, detailed=True)
            else:
                print(f"❌ User {user_id} not found in results")
        else:
            # Summary report
            total_users = process_results["total_users"]
            users_with_discrepancies = process_results["users_with_discrepancies"]
            
            print(f"📊 Total users processed: {total_users}")
            
            if self.update_mode:
                users_updated = process_results["users_updated"]
                users_with_errors = process_results["users_with_errors"]
                print(f"✅ Users updated: {users_updated}")
                print(f"❌ Users with errors: {users_with_errors}")
                print(f"📝 Total database updates: {process_results['updates_made']}")
                
                if users_updated > 0:
                    print(f"\n🔧 Users that were updated:")
                    for uid, result in process_results["results"].items():
                        if result.get("status") == "updated":
                            self.print_user_result(result, detailed=detailed)
                
                if users_with_errors > 0:
                    print(f"\n❌ Users with errors:")
                    for uid, result in process_results["results"].items():
                        if result.get("status") == "error":
                            self.print_user_result(result, detailed=True)
            else:
                print(f"✅ Users with matching stats: {total_users - users_with_discrepancies}")
                print(f"❌ Users with discrepancies: {users_with_discrepancies}")
                
                if users_with_discrepancies > 0:
                    print(f"\n🔍 Users with discrepancies:")
                    for uid, result in process_results["results"].items():
                        if result.get("has_discrepancies", False):
                            self.print_user_result(result, detailed=detailed)
            
            if detailed:
                print(f"\n📋 All users:")
                for uid, result in process_results["results"].items():
                    self.print_user_result(result, detailed=False)
    
    def print_user_result(self, result: Dict[str, Any], detailed: bool = False):
        """Print result for a single user"""
        username = result.get("username", "Unknown")
        user_id = result.get("user_id", "Unknown")
        status = result.get("status", "unknown")
        has_discrepancies = result.get("has_discrepancies", False)
        
        if self.update_mode:
            # Update mode reporting
            if status == "updated":
                update_data = result.get("update_data", {})
                print(f"\n✅ {username} (ID: {user_id}): Updated successfully")
                if detailed:
                    for field, value in update_data.items():
                        print(f"  - {field}: {value}")
            elif status == "dry_run":
                update_data = result.get("update_data", {})
                print(f"\n🔍 {username} (ID: {user_id}): Would be updated")
                if detailed:
                    for field, value in update_data.items():
                        print(f"  - {field}: {value}")
            elif status == "no_changes_needed":
                print(f"\n✅ {username} (ID: {user_id}): No changes needed")
            elif status == "error":
                error = result.get("error", "Unknown error")
                print(f"\n❌ {username} (ID: {user_id}): Error - {error}")
            else:
                print(f"\n❓ {username} (ID: {user_id}): Status - {status}")
        else:
            # Validation mode reporting
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
    parser = argparse.ArgumentParser(description="Validate and optionally update user statistics")
    parser.add_argument("--validate-only", action="store_true", 
                       help="Only validate statistics without updating (default behavior)")
    parser.add_argument("--update", action="store_true", 
                       help="Update database with correct statistics")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Show what would be updated without making changes (requires --update)")
    parser.add_argument("--detailed", action="store_true", 
                       help="Show detailed output for all users")
    parser.add_argument("--user-id", type=str, 
                       help="Process only specific user ID")
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.dry_run and not args.update:
        print("❌ Error: --dry-run requires --update flag")
        sys.exit(1)
    
    if args.update and args.validate_only:
        print("❌ Error: Cannot use both --update and --validate-only flags")
        sys.exit(1)
    
    # Determine mode
    update_mode = args.update
    dry_run = args.dry_run
    
    try:
        manager = UserStatsManager(update_mode=update_mode, dry_run=dry_run)
        await manager.initialize()
        
        if args.user_id:
            # Process single user
            action = "Updating" if update_mode else "Validating"
            logger.info(f"{action} user: {args.user_id}")
            result = await manager.process_user(args.user_id)
            
            if update_mode:
                process_results = {
                    "total_users": 1,
                    "users_with_discrepancies": 1 if result.get("has_discrepancies", False) else 0,
                    "users_updated": 1 if result.get("status") == "updated" else 0,
                    "users_with_errors": 1 if result.get("status") == "error" else 0,
                    "updates_made": 1 if result.get("status") == "updated" else 0,
                    "results": {args.user_id: result}
                }
            else:
                process_results = {
                    "total_users": 1,
                    "users_with_discrepancies": 1 if result.get("has_discrepancies", False) else 0,
                    "results": {args.user_id: result}
                }
            
            manager.print_report(process_results, detailed=True, user_id=args.user_id)
        else:
            # Process all users
            process_results = await manager.process_all_users()
            manager.print_report(process_results, detailed=args.detailed)
        
        # Final message
        if update_mode and not dry_run:
            print(f"\n📝 Database has been updated with correct user statistics.")
        elif not update_mode:
            print(f"\n📝 Note: This was a validation run - no changes were made to the database.")
        
        print(f"🕒 Processing completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except KeyboardInterrupt:
        logger.info("Processing interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Processing failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
