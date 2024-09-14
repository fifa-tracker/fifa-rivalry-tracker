import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import os

# MongoDB connection
client = AsyncIOMotorClient(
    os.getenv("MONGO_URI", "mongodb://mongodb:27017/fifa_rivalry")
)
db = client.fifa_rivalry

async def backport_goal_difference():
    players = await db.players.find().to_list(1000)
    
    for player in players:
        goal_difference = player['total_goals_scored'] - player['total_goals_conceded']
        
        await db.players.update_one(
            {"_id": player["_id"]},
            {"$set": {"goal_difference": goal_difference}}
        )
        
        print(f"Updated goal difference for player {player['name']}: {goal_difference}")

async def main():
    print("Starting goal difference backport...")
    await backport_goal_difference()
    print("Goal difference backport completed.")

if __name__ == "__main__":
    asyncio.run(main())