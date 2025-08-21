from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv
import re
import urllib.parse
import json

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configure Ollama
OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'mistral:latest')

# Craigslist configuration
DEFAULT_CITY = "sfbay"  # San Francisco Bay Area
CITY_MAPPING = {
    "san francisco": "sfbay",
    "sf": "sfbay",
    "bay area": "sfbay",
    "new york": "nyc",
    "nyc": "nyc",
    "los angeles": "losangeles",
    "la": "losangeles",
    "chicago": "chicago",
    "seattle": "seattle",
    "austin": "austin",
    "denver": "denver",
    "miami": "miami",
    "atlanta": "atlanta",
    "phoenix": "phoenix",
    "dallas": "dallas",
    "houston": "houston"
}

# Category mapping for common searches
CATEGORY_MAPPING = {
    "car": "cta",  # cars & trucks
    "vehicle": "cta",
    "automobile": "cta",
    "laptop": "sys",  # computers
    "computer": "sys",
    "desktop": "sys",
    "furniture": "fua",  # furniture
    "couch": "fua",
    "table": "fua",
    "chair": "fua",
    "apartment": "apa",  # apartments
    "rental": "apa",
    "house": "rea",  # real estate
    "home": "rea",
    "job": "jjj",  # jobs
    "employment": "jjj",
    "work": "jjj"
}

def extract_city_from_query(query):
    """Extract city from user query if mentioned"""
    query_lower = query.lower()
    for city_name, city_code in CITY_MAPPING.items():
        if city_name in query_lower:
            return city_code
    return DEFAULT_CITY

def extract_category_from_query(query):
    """Extract category from user query if mentioned"""
    query_lower = query.lower()
    for category_name, category_code in CATEGORY_MAPPING.items():
        if category_name in query_lower:
            return category_code
    return None

def extract_zip_code_from_query(query):
    """Extract zip code from user query"""
    import re
    # Look for 5-digit zip codes
    zip_pattern = r'\b\d{5}\b'
    zip_match = re.search(zip_pattern, query)
    if zip_match:
        return zip_match.group()
    return None

def extract_radius_from_query(query):
    """Extract radius from user query"""
    import re
    query_lower = query.lower()
    
    # Common radius patterns
    radius_patterns = [
        (r'(\d+)\s*miles?', 1),      # "5 miles", "10 mile"
        (r'(\d+)\s*mi', 1),          # "5 mi", "10 mi"
        (r'(\d+)\s*mile\s*radius', 1), # "5 mile radius"
        (r'within\s*(\d+)\s*miles?', 1), # "within 5 miles"
        (r'(\d+)\s*mile\s*area', 1), # "5 mile area"
        (r'(\d+)\s*km', 0.621371),   # "5 km" -> convert to miles
        (r'(\d+)\s*kilometers?', 0.621371), # "5 kilometers" -> convert to miles
    ]
    
    for pattern, multiplier in radius_patterns:
        match = re.search(pattern, query_lower)
        if match:
            radius_value = int(match.group(1)) * multiplier
            return int(radius_value)
    
    return None

def generate_craigslist_link(keywords, city, category, min_price=None, max_price=None, zip_code=None, radius=None):
    """Generate a Craigslist search URL with zip code and radius support"""
    # Clean and format keywords
    formatted_keywords = "|".join([kw.strip().replace(" ", "+") for kw in keywords if kw.strip()])
    
    # Build base URL
    base_url = f"https://{city}.craigslist.org/search/{category or 'sss'}"
    
    # Build query parameters
    params = []
    if formatted_keywords:
        params.append(f"query={formatted_keywords}")
    if min_price is not None:
        params.append(f"min_price={min_price}")
    if max_price is not None:
        params.append(f"max_price={max_price}")
    if zip_code:
        params.append(f"postal={zip_code}")
    if radius:
        params.append(f"search_distance={radius}")
    
    # Combine URL and parameters
    if params:
        return f"{base_url}?{'&'.join(params)}"
    return base_url

@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')

@app.route('/api/generate-link', methods=['POST'])
def generate_link():
    """Generate Craigslist link based on user query"""
    try:
        data = request.get_json()
        user_query = data.get('query', '').strip()
        
        if not user_query:
            return jsonify({'error': 'Query is required'}), 400
        
        # Extract city, category, zip code, and radius from query
        city = extract_city_from_query(user_query)
        category = extract_category_from_query(user_query)
        zip_code = extract_zip_code_from_query(user_query)
        radius = extract_radius_from_query(user_query)
        
        # Prepare prompt for Ollama Mistral 7B
        system_prompt = """Extract from user request: 3-5 specific item recommendations, price range (min/max), and Craigslist category. Return JSON only:
        {"recommendations": ["item1", "item2", "item3"], "min_price": null or number, "max_price": null or number, "category": "category_code", "explanation": "Brief explanation"}
        
        Categories: cta (cars), sys (computers), fua (furniture), apa (apartments), rea (real estate), jjj (jobs), sss (general search)"""
        
        user_prompt = f"User request: {user_query}"
        
        # Call Ollama API
        ollama_payload = {
            "model": OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_predict": 150,  # Reduced for faster responses
                "top_k": 10,         # Limit token selection for speed
                "top_p": 0.9,        # Nucleus sampling for efficiency
                "repeat_penalty": 1.1 # Prevent repetitive responses
            }
        }
        
        try:
            response = requests.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json=ollama_payload,
                timeout=120  # Increased timeout to 2 minutes
            )
            response.raise_for_status()
            
            # Parse Ollama response
            ai_response = response.json()['message']['content'].strip()
            
        except requests.exceptions.Timeout:
            raise Exception("Request timed out. Ollama model is still processing. Try again in a moment.")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Ollama API error: {str(e)}")
        except KeyError as e:
            raise Exception(f"Invalid response from Ollama: {str(e)}")
        
        # Try to extract JSON from response
        try:
            # Find JSON in the response
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                import json
                parsed_response = json.loads(json_match.group())
            else:
                # Fallback parsing
                parsed_response = {
                    "recommendations": ["item1", "item2", "item3"],
                    "min_price": None,
                    "max_price": None,
                    "category": category or "sss",
                    "explanation": ai_response
                }
        except:
            # Fallback if JSON parsing fails
            parsed_response = {
                "recommendations": ["item1", "item2", "item3"],
                "min_price": None,
                "max_price": None,
                "category": category or "sss",
                "explanation": ai_response
            }
        
        # Generate individual Craigslist links for each recommendation
        recommendations = parsed_response.get("recommendations", [])
        craigslist_links = []
        
        for item in recommendations:
            if item and item.strip():  # Skip empty items
                individual_url = generate_craigslist_link(
                    [item],  # Single item
                    city,
                    parsed_response.get("category", category) or "sss",
                    parsed_response.get("min_price"),
                    parsed_response.get("max_price"),
                    zip_code,  # Include zip code
                    radius     # Include radius
                )
                craigslist_links.append({
                    "item": item,
                    "url": individual_url
                })
        
        # Prepare response
        result = {
            "success": True,
            "query": user_query,
            "recommendations": recommendations,
            "explanation": parsed_response.get("explanation", ""),
            "craigslist_links": craigslist_links,  # Multiple individual links
            "city": city,
            "category": parsed_response.get("category", category) or "sss",
            "min_price": parsed_response.get("min_price"),
            "max_price": parsed_response.get("max_price"),
            "zip_code": zip_code,
            "radius": radius
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'error': f'An error occurred: {str(e)}',
            'success': False
        }), 500

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'AI Craigslist Link Generator'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
