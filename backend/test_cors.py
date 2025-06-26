#!/usr/bin/env python3
"""
Test script to verify CORS configuration.
Run this to test your CORS setup before deployment.
"""

import os
import requests
import json
from app.config import get_settings

def test_cors_configuration():
    """Test CORS configuration for different environments."""
    
    print("🔍 Testing CORS Configuration")
    print("=" * 50)
    
    # Test different environments
    environments = [
        ("development", {}),
        ("production", {"ENVIRONMENT": "production"})
    ]
    
    for env_name, env_vars in environments:
        print(f"\n📋 Testing {env_name.upper()} environment:")
        
        # Set environment variables
        for key, value in env_vars.items():
            os.environ[key] = value
        
        try:
            # Get settings
            settings = get_settings()
            print(f"  ✅ CORS Origins: {settings.cors_origins}")
            print(f"  ✅ Debug Mode: {settings.debug}")
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
        
        # Clean up environment
        for key in env_vars:
            if key in os.environ:
                del os.environ[key]
    
    print("\n" + "=" * 50)
    print("✅ CORS Configuration Test Complete")

def test_cors_headers(api_url="http://localhost:8000"):
    """Test actual CORS headers from your API."""
    
    print(f"\n🌐 Testing CORS Headers against {api_url}")
    print("=" * 50)
    
    try:
        # Test preflight request
        headers = {
            "Origin": "https://nobellm.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type"
        }
        
        response = requests.options(f"{api_url}/api/query", headers=headers)
        
        print(f"  📡 Status Code: {response.status_code}")
        print(f"  🔗 Access-Control-Allow-Origin: {response.headers.get('Access-Control-Allow-Origin', 'NOT SET')}")
        print(f"  🔗 Access-Control-Allow-Methods: {response.headers.get('Access-Control-Allow-Methods', 'NOT SET')}")
        print(f"  🔗 Access-Control-Allow-Headers: {response.headers.get('Access-Control-Allow-Headers', 'NOT SET')}")
        print(f"  🔗 Access-Control-Allow-Credentials: {response.headers.get('Access-Control-Allow-Credentials', 'NOT SET')}")
        
        if response.status_code == 200:
            print("  ✅ CORS preflight successful")
        else:
            print("  ❌ CORS preflight failed")
            
    except requests.exceptions.ConnectionError:
        print("  ⚠️  Could not connect to API. Make sure it's running on localhost:8000")
    except Exception as e:
        print(f"  ❌ Error testing CORS headers: {e}")

if __name__ == "__main__":
    test_cors_configuration()
    test_cors_headers() 