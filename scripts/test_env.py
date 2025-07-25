#!/usr/bin/env python3
"""
Test script to verify environment variables are loaded correctly.
This helps debug configuration issues in deployment.
"""

import os
from pathlib import Path
from dotenv import dotenv_values

def test_env_loading():
    """Test environment variable loading"""
    print("🔍 Testing Environment Variable Loading")
    print("=" * 50)
    
    # Test 1: Direct environment variables
    print("\n1️⃣ Direct Environment Variables:")
    print("-" * 30)
    env_vars = ["ENVIRONMENT", "MONGO_URI", "SECRET_KEY", "ACCESS_TOKEN_EXPIRE_MINUTES", "LOG_LEVEL"]
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if var in ["MONGO_URI", "SECRET_KEY"]:
                masked_value = value[:10] + "..." + value[-10:] if len(value) > 20 else "***"
                print(f"✅ {var}: {masked_value}")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: Not set")
    
    # Test 2: .env file loading
    print("\n2️⃣ .env File Loading:")
    print("-" * 30)
    env_path = Path(__file__).parent.parent / '.env'
    
    if env_path.exists():
        print(f"✅ .env file found at: {env_path}")
        config = dotenv_values(env_path)
        print(f"✅ Loaded {len(config)} variables from .env file")
        
        for var in env_vars:
            value = config.get(var)
            if value:
                # Mask sensitive values
                if var in ["MONGO_URI", "SECRET_KEY"]:
                    masked_value = value[:10] + "..." + value[-10:] if len(value) > 20 else "***"
                    print(f"  ✅ {var}: {masked_value}")
                else:
                    print(f"  ✅ {var}: {value}")
            else:
                print(f"  ❌ {var}: Not found in .env")
    else:
        print(f"❌ .env file not found at: {env_path}")
    
    # Test 3: Combined loading (like the app does)
    print("\n3️⃣ Combined Loading (App Method):")
    print("-" * 30)
    
    config = dotenv_values(env_path) if env_path.exists() else {}
    
    def get_env_var(key: str, default: str = None) -> str:
        """Get environment variable with fallback to .env file"""
        return os.getenv(key, config.get(key, default))
    
    for var in env_vars:
        value = get_env_var(var)
        if value:
            # Mask sensitive values
            if var in ["MONGO_URI", "SECRET_KEY"]:
                masked_value = value[:10] + "..." + value[-10:] if len(value) > 20 else "***"
                print(f"✅ {var}: {masked_value}")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: Not set")
    
    # Test 4: Critical validation
    print("\n4️⃣ Critical Validation:")
    print("-" * 30)
    
    mongo_uri = get_env_var("MONGO_URI")
    secret_key = get_env_var("SECRET_KEY")
    environment = get_env_var("ENVIRONMENT", "development")
    
    if mongo_uri:
        print("✅ MONGO_URI is set")
    else:
        print("❌ MONGO_URI is missing - this will cause the app to fail!")
    
    if secret_key and secret_key != "your-secret-key-here-change-in-production":
        print("✅ SECRET_KEY is set and changed from default")
    elif secret_key:
        print("⚠️  SECRET_KEY is set but still using default value")
    else:
        print("❌ SECRET_KEY is missing")
    
    if environment == "production":
        if secret_key and secret_key != "your-secret-key-here-change-in-production":
            print("✅ Production environment with proper SECRET_KEY")
        else:
            print("❌ Production environment but SECRET_KEY not properly configured!")
    else:
        print(f"ℹ️  Environment: {environment}")
    
    print("\n" + "=" * 50)
    print("📝 Summary:")
    if mongo_uri and secret_key:
        print("✅ All critical variables are set - app should start successfully")
    else:
        print("❌ Missing critical variables - app will fail to start")
        if not mongo_uri:
            print("   - MONGO_URI is required")
        if not secret_key:
            print("   - SECRET_KEY is required")

if __name__ == "__main__":
    test_env_loading() 