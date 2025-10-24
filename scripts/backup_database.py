#!/usr/bin/env python3
"""
Database Backup Script for FIFA Rivalry Tracker

This script creates comprehensive backups of the MongoDB database including:
1. Binary BSON backup using mongodump
2. JSON exports for readability and inspection

Usage:
    python scripts/backup_database.py

Requirements:
    - MongoDB tools (mongodump) installed
    - Valid MONGO_URI environment variable or .env file
"""

import os
import sys
import json
import subprocess
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
import asyncio

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.config import settings
from app.api.dependencies import get_database
from app.utils.logging import get_logger

logger = get_logger(__name__)


class DatabaseBackup:
    """Handles database backup operations"""
    
    def __init__(self):
        self.backup_dir = None
        self.timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.collections = ["users", "matches", "tournaments"]
        
    def create_backup_directory(self) -> Path:
        """Create timestamped backup directory"""
        backup_base = project_root / "backups"
        backup_base.mkdir(exist_ok=True)
        
        self.backup_dir = backup_base / self.timestamp
        self.backup_dir.mkdir(exist_ok=True)
        
        logger.info(f"Created backup directory: {self.backup_dir}")
        return self.backup_dir
    
    def check_mongodump_available(self) -> bool:
        """Check if mongodump is available in the system"""
        try:
            result = subprocess.run(["mongodump", "--version"], 
                                 capture_output=True, text=True, check=True)
            logger.info("mongodump is available")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.warning("mongodump not found. BSON backup will be skipped.")
            return False
    
    def create_bson_backup(self) -> bool:
        """Create BSON backup using mongodump"""
        if not self.check_mongodump_available():
            return False
            
        try:
            # Extract host and port from MONGO_URI
            mongo_uri = settings.MONGO_URI
            if not mongo_uri:
                logger.error("MONGO_URI not configured")
                return False
            
            # Parse MongoDB URI to extract connection details
            # Format: mongodb://[username:password@]host[:port]/database
            if mongo_uri.startswith("mongodb://"):
                uri_parts = mongo_uri.replace("mongodb://", "").split("/")
                connection_part = uri_parts[0]
                database_part = uri_parts[1] if len(uri_parts) > 1 else settings.DATABASE_NAME
                
                # Handle authentication
                if "@" in connection_part:
                    auth_part, host_part = connection_part.split("@", 1)
                    username, password = auth_part.split(":", 1)
                    host_port = host_part
                else:
                    username = password = None
                    host_port = connection_part
                
                # Extract host and port
                if ":" in host_port:
                    host, port = host_port.split(":", 1)
                else:
                    host, port = host_port, "27017"
            else:
                logger.error("Invalid MONGO_URI format")
                return False
            
            # Build mongodump command
            cmd = [
                "mongodump",
                "--host", f"{host}:{port}",
                "--db", database_part,
                "--out", str(self.backup_dir / "bson")
            ]
            
            if username and password:
                cmd.extend(["--username", username, "--password", password])
            
            logger.info(f"Running mongodump command: {' '.join(cmd[:4])}...")
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info("BSON backup completed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"mongodump failed: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Error creating BSON backup: {str(e)}")
            return False
    
    async def export_collection_to_json(self, db, collection_name: str) -> bool:
        """Export a collection to JSON format"""
        try:
            logger.info(f"Exporting {collection_name} collection to JSON...")
            
            # Get all documents from the collection
            cursor = db[collection_name].find({})
            documents = await cursor.to_list(length=None)
            
            # Convert ObjectId to string for JSON serialization
            def convert_objectid(obj):
                if isinstance(obj, dict):
                    return {k: convert_objectid(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_objectid(item) for item in obj]
                elif hasattr(obj, '__str__') and 'ObjectId' in str(type(obj)):
                    return str(obj)
                else:
                    return obj
            
            # Convert documents
            json_docs = [convert_objectid(doc) for doc in documents]
            
            # Write to JSON file
            json_file = self.backup_dir / f"{collection_name}.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(json_docs, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"Exported {len(json_docs)} documents from {collection_name} to {json_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting {collection_name}: {str(e)}")
            return False
    
    async def create_json_backups(self) -> bool:
        """Create JSON backups for all collections"""
        try:
            db = await get_database()
            
            success_count = 0
            for collection_name in self.collections:
                if await self.export_collection_to_json(db, collection_name):
                    success_count += 1
            
            logger.info(f"JSON backup completed: {success_count}/{len(self.collections)} collections exported")
            return success_count == len(self.collections)
            
        except Exception as e:
            logger.error(f"Error creating JSON backups: {str(e)}")
            return False
    
    def create_backup_info(self) -> None:
        """Create backup information file"""
        try:
            info = {
                "backup_timestamp": self.timestamp,
                "database_name": settings.DATABASE_NAME,
                "environment": settings.ENVIRONMENT,
                "collections_backed_up": self.collections,
                "backup_location": str(self.backup_dir),
                "created_at": datetime.now().isoformat()
            }
            
            info_file = self.backup_dir / "backup_info.json"
            with open(info_file, 'w', encoding='utf-8') as f:
                json.dump(info, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Created backup info file: {info_file}")
            
        except Exception as e:
            logger.error(f"Error creating backup info: {str(e)}")
    
    async def run_backup(self) -> bool:
        """Run the complete backup process"""
        try:
            logger.info("Starting database backup process...")
            
            # Create backup directory
            self.create_backup_directory()
            
            # Create BSON backup
            bson_success = self.create_bson_backup()
            
            # Create JSON backups
            json_success = await self.create_json_backups()
            
            # Create backup info
            self.create_backup_info()
            
            # Summary
            if bson_success and json_success:
                logger.info(f"✅ Backup completed successfully!")
                logger.info(f"📁 Backup location: {self.backup_dir}")
                logger.info(f"📊 Collections backed up: {', '.join(self.collections)}")
                return True
            elif json_success:
                logger.warning("⚠️  JSON backup completed, but BSON backup failed")
                logger.info(f"📁 Backup location: {self.backup_dir}")
                return True
            else:
                logger.error("❌ Backup failed")
                return False
                
        except Exception as e:
            logger.error(f"Backup process failed: {str(e)}")
            return False


async def main():
    """Main function"""
    try:
        backup = DatabaseBackup()
        success = await backup.run_backup()
        
        if success:
            print(f"\n✅ Database backup completed successfully!")
            print(f"📁 Backup location: {backup.backup_dir}")
            sys.exit(0)
        else:
            print(f"\n❌ Database backup failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Backup interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
