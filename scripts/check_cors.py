#!/usr/bin/env python3
"""
Script to check and debug CORS configuration
"""

import os
from pathlib import Path
from dotenv import dotenv_values

def check_cors_config():
    """Check CORS configuration from environment and .env files"""
    
    print("🔍 Checking CORS Configuration...")
    print("=" * 50)
    
    # Check environment variables
    cors_env = os.getenv("CORS_ORIGINS")
    if cors_env:
        print(f"❌ Found CORS_ORIGINS environment variable: {cors_env}")
        origins = [origin.strip() for origin in cors_env.split(",")]
        print(f"   Parsed origins: {origins}")
        
        # Check for wildcards
        wildcards = [origin for origin in origins if origin == "*"]
        if wildcards:
            print(f"   ⚠️  Found wildcard origins: {wildcards}")
            print("   This can cause CORS issues when combined with specific origins")
        
        # Check for duplicates
        if len(origins) != len(set(origins)):
            print("   ⚠️  Found duplicate origins")
    else:
        print("✅ No CORS_ORIGINS environment variable found")
    
    # Check .env file
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        print(f"\n📄 Checking .env file: {env_path}")
        config = dotenv_values(env_path)
        if "CORS_ORIGINS" in config:
            print(f"❌ Found CORS_ORIGINS in .env: {config['CORS_ORIGINS']}")
        else:
            print("✅ No CORS_ORIGINS in .env file")
    else:
        print(f"\n📄 No .env file found at: {env_path}")
    
    # Check current working directory .env
    cwd_env = Path.cwd() / '.env'
    if cwd_env.exists() and cwd_env != env_path:
        print(f"\n📄 Checking current directory .env: {cwd_env}")
        config = dotenv_values(cwd_env)
        if "CORS_ORIGINS" in config:
            print(f"❌ Found CORS_ORIGINS in current .env: {config['CORS_ORIGINS']}")
        else:
            print("✅ No CORS_ORIGINS in current .env file")
    
    print("\n" + "=" * 50)
    print("💡 Recommendations:")
    print("1. Remove any CORS_ORIGINS environment variable that contains wildcards (*)")
    print("2. Ensure CORS_ORIGINS only contains specific domains")
    print("3. Restart your FastAPI server after making changes")
    print("4. Check the /cors-debug endpoint to verify configuration")

if __name__ == "__main__":
    check_cors_config() 