#!/usr/bin/env python3
"""
Demo script for the AI Craigslist Link Generator
Shows example queries and expected outputs
"""

import json
import requests
import time

def demo_queries():
    """Show example queries and their expected outputs"""
    
    examples = [
        {
            "query": "I want a reliable car under $10,000",
            "description": "Car search with budget constraint",
            "expected_category": "cta",
            "expected_city": "sfbay"
        },
        {
            "query": "cheap laptop for coding under $500",
            "description": "Laptop search for development work",
            "expected_category": "sys",
            "expected_city": "sfbay"
        },
        {
            "query": "furniture for small apartment in NYC",
            "description": "Furniture search in New York",
            "expected_category": "fua",
            "expected_city": "nyc"
        },
        {
            "query": "remote software job in Seattle",
            "description": "Job search in Seattle area",
            "expected_category": "jjj",
            "expected_city": "seattle"
        },
        {
            "query": "apartment for rent in Los Angeles under $2000",
            "description": "Apartment rental with price limit",
            "expected_category": "apa",
            "expected_city": "losangeles"
        }
    ]
    
    print("🚀 AI Craigslist Link Generator - Demo Examples")
    print("=" * 60)
    print()
    
    for i, example in enumerate(examples, 1):
        print(f"Example {i}: {example['description']}")
        print(f"Query: \"{example['query']}\"")
        print(f"Expected Category: {example['expected_category']}")
        print(f"Expected City: {example['expected_city']}")
        print("-" * 40)
    
    print()
    print("💡 Try these queries in the web interface!")
    print("   The AI will automatically detect categories, cities, and price ranges.")
    print()

def test_api_endpoints():
    """Test the API endpoints if the app is running"""
    
    print("🧪 Testing API Endpoints")
    print("=" * 40)
    
    base_url = "http://localhost:5000"
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health endpoint: Working")
            health_data = response.json()
            print(f"   Service: {health_data.get('service', 'Unknown')}")
        else:
            print(f"❌ Health endpoint: Failed (Status: {response.status_code})")
    except requests.exceptions.ConnectionError:
        print("❌ Health endpoint: Cannot connect (App not running)")
    except Exception as e:
        print(f"❌ Health endpoint: Error - {e}")
    
    print()
    
    # Test generate link endpoint with sample query
    try:
        test_query = "reliable car under $10,000"
        payload = {"query": test_query}
        
        response = requests.post(
            f"{base_url}/api/generate-link",
            headers={'Content-Type': 'application/json'},
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Generate link endpoint: Working")
                print(f"   Query: {data.get('query')}")
                print(f"   Recommendations: {', '.join(data.get('recommendations', []))}")
                print(f"   City: {data.get('city')}")
                print(f"   Category: {data.get('category')}")
                print(f"   Max Price: ${data.get('max_price', 'N/A')}")
                print(f"   Craigslist URL: {data.get('craigslist_url')}")
            else:
                print(f"❌ Generate link endpoint: Failed - {data.get('error')}")
        else:
            print(f"❌ Generate link endpoint: Failed (Status: {response.status_code})")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Generate link endpoint: Cannot connect (App not running)")
    except requests.exceptions.Timeout:
        print("❌ Generate link endpoint: Timeout (Ollama model might be slow)")
    except Exception as e:
        print(f"❌ Generate link endpoint: Error - {e}")
    
    print()

def show_usage_instructions():
    """Show how to use the application"""
    
    print("📖 How to Use")
    print("=" * 40)
    
    print("1. Start the application:")
    print("   python app.py")
    print("   # or use the startup script:")
    print("   ./start.sh")
    print()
    
    print("2. Open your browser to: http://localhost:5000")
    print()
    
    print("3. Type a description of what you're looking for:")
    print("   - Be specific about what you want")
    print("   - Mention your budget if applicable")
    print("   - Include location if you want a specific city")
    print()
    
    print("4. Click 'Generate Link' or press Enter")
    print()
    
    print("5. The AI will:")
    print("   - Analyze your request")
    print("   - Suggest relevant items/brands")
    print("   - Generate an optimized Craigslist search link")
    print()
    
    print("6. Click the generated link to view results on Craigslist")
    print()

def main():
    """Main demo function"""
    
    print("🤖 AI Craigslist Link Generator Bot")
    print("=" * 50)
    print()
    
    # Show demo examples
    demo_queries()
    
    # Show usage instructions
    show_usage_instructions()
    
    # Test API if app is running
    test_api_endpoints()
    
    print("🎯 Ready to generate some Craigslist links!")
    print("   Start the application and try the examples above.")
    print()

if __name__ == "__main__":
    main()
