#!/usr/bin/env python3
"""
Dependency Update Script for FIFA Rivalry Tracker
This script helps update dependencies and fix compatibility issues.
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"   Error: {e}")
        if e.stderr:
            print(f"   Stderr: {e.stderr}")
        return False

def main():
    print("=" * 60)
    print("Dependency Update Script for FIFA Rivalry Tracker")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not os.path.exists("pyproject.toml"):
        print("❌ Error: pyproject.toml not found. Please run this script from the project root.")
        sys.exit(1)
    
    # Update dependencies
    commands = [
        ("uv lock --no-update", "Locking dependencies"),
        ("uv sync --upgrade", "Upgrading dependencies"),
        ("uv sync", "Syncing dependencies"),
    ]
    
    success = True
    for command, description in commands:
        if not run_command(command, description):
            success = False
            break
    
    if success:
        print("\n🎉 All dependencies updated successfully!")
        print("\nNext steps:")
        print("1. Restart your FastAPI server")
        print("2. Test CORS functionality")
        print("3. Check that bcrypt warnings are resolved")
    else:
        print("\n❌ Some dependency updates failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main() 