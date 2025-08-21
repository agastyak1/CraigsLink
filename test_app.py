#!/usr/bin/env python3
"""
Simple test script for the AI Craigslist Link Generator
"""

import requests
import json
import time
import sys

def test_health_endpoint():
    """Test the health check endpoint"""
    try:
        response = requests.get('http://localhost:5000/api/health')
        if response.status_code == 200:
            print("✅ Health check endpoint working")
            return True
        else:
            print(f"❌ Health check failed with status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to application. Is it running?")
        return False

def test_generate_link_endpoint():
    """Test the generate link endpoint with a sample query"""
    try:
        test_query = "reliable car under $10,000"
        payload = {"query": test_query}
        
        response = requests.post(
            'http://localhost:5000/api/generate-link',
            headers={'Content-Type': 'application/json'},
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Generate link endpoint working")
                print(f"   Query: {data.get('query')}")
                print(f"   Recommendations: {data.get('recommendations', [])}")
                print(f"   Craigslist URL: {data.get('craigslist_url')}")
                return True
            else:
                print(f"❌ Generate link failed: {data.get('error')}")
                return False
        else:
            print(f"❌ Generate link endpoint failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to application. Is it running?")
        return False
    except requests.exceptions.Timeout:
        print("❌ Request timed out. OpenAI API might be slow.")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing AI Craigslist Link Generator...")
    print("=" * 50)
    
    # Wait a moment for app to be ready
    print("⏳ Waiting for application to be ready...")
    time.sleep(2)
    
    # Test health endpoint
    health_ok = test_health_endpoint()
    
    if health_ok:
        # Test generate link endpoint
        generate_ok = test_generate_link_endpoint()
        
        if generate_ok:
            print("\n🎉 All tests passed! Application is working correctly.")
            return 0
        else:
            print("\n⚠️  Health check passed but generate link failed.")
            print("   This might be due to missing OpenAI API key or API issues.")
            return 1
    else:
        print("\n❌ Basic connectivity test failed.")
        print("   Make sure the Flask application is running on port 5000.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
