#!/usr/bin/env python3
"""
Script to test CORS configuration from frontend perspective
"""

import requests
import json

def test_cors_from_frontend():
    """Test CORS configuration by simulating frontend requests"""
    
    # Your ngrok URL from the error message
    base_url = "https://25078b6fce82.ngrok-free.app"
    
    # Test endpoints
    endpoints = [
        "/",
        "/cors-debug",
        "/cors-test",
        "/api/v1/auth/login"
    ]
    
    print("🧪 Testing CORS Configuration...")
    print("=" * 60)
    print(f"Testing against: {base_url}")
    print()
    
    # Headers that simulate a frontend request
    headers = {
        "Origin": "https://fifa-tracker-qcdulk1cy-roshan-johns-projects.vercel.app",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    for endpoint in endpoints:
        url = f"{base_url}{endpoint}"
        print(f"🔍 Testing: {endpoint}")
        
        try:
            # Make a GET request
            response = requests.get(url, headers=headers, timeout=10)
            
            print(f"   Status: {response.status_code}")
            print(f"   CORS Headers:")
            
            # Check CORS headers
            cors_headers = {
                "Access-Control-Allow-Origin": response.headers.get("Access-Control-Allow-Origin"),
                "Access-Control-Allow-Credentials": response.headers.get("Access-Control-Allow-Credentials"),
                "Access-Control-Allow-Methods": response.headers.get("Access-Control-Allow-Methods"),
                "Access-Control-Allow-Headers": response.headers.get("Access-Control-Allow-Headers"),
            }
            
            for header, value in cors_headers.items():
                if value:
                    print(f"     {header}: {value}")
                else:
                    print(f"     {header}: Not set")
            
            # Check for multiple Access-Control-Allow-Origin headers
            # Note: requests doesn't have get_all, but we can check if the header contains multiple values
            origin_header = response.headers.get("Access-Control-Allow-Origin")
            if origin_header and "," in origin_header:
                print(f"   ⚠️  WARNING: Multiple Access-Control-Allow-Origin values found: {origin_header}")
            elif origin_header:
                print(f"   ✅ Single Access-Control-Allow-Origin value: {origin_header}")
            
            # Try to parse JSON response
            try:
                data = response.json()
                if endpoint == "/cors-debug":
                    print(f"   CORS Origins from server: {data.get('cors_origins', 'Not found')}")
            except:
                pass
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Error: {e}")
        
        print()
    
    print("=" * 60)
    print("💡 If you see multiple Access-Control-Allow-Origin headers,")
    print("   that's the cause of your CORS error. Restart your server")
    print("   after applying the fixes.")

if __name__ == "__main__":
    test_cors_from_frontend() 