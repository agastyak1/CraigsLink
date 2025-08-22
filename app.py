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
    # Vehicles
    "car": "cta",  # cars & trucks
    "vehicle": "cta",
    "automobile": "cta",
    "truck": "cta",
    "motorcycle": "mca",  # motorcycles
    "boat": "boa",  # boats
    "rv": "rva",  # RVs
    
    # Electronics & Computers
    "laptop": "sys",  # computers
    "computer": "sys",
    "desktop": "sys",
    "iphone": "moa",  # mobile phones
    "phone": "moa",
    "mobile": "moa",
    "smartphone": "moa",
    "android": "moa",
    "apple": "moa",
    "ipad": "moa",
    "tablet": "moa",
    "watch": "jwa",  # jewelry & watches
    "apple watch": "jwa",
    "headphones": "ele",  # electronics
    "camera": "ele",
    "tv": "ele",
    "television": "ele",
    "gaming": "ele",
    "xbox": "ele",
    "playstation": "ele",
    "nintendo": "ele",
    
    # Furniture & Home
    "furniture": "fua",  # furniture
    "couch": "fua",
    "sofa": "fua",
    "table": "fua",
    "chair": "fua",
    "bed": "fua",
    "mattress": "fua",
    "dresser": "fua",
    "kitchen": "fua",
    "appliance": "fua",
    "refrigerator": "fua",
    "washer": "fua",
    "dryer": "fua",
    
    # Housing
    "apartment": "apa",  # apartments
    "rental": "apa",
    "house": "rea",  # real estate
    "home": "rea",
    "condo": "rea",
    "townhouse": "rea",
    "room": "roo",  # rooms
    "sublet": "roo",
    
    # Jobs
    "job": "jjj",  # jobs
    "employment": "jjj",
    "work": "jjj",
    "career": "jjj",
    "position": "jjj",
    
    # Services
    "service": "sks",  # skilled trades
    "repair": "sks",
    "cleaning": "sks",
    "plumbing": "sks",
    "electrical": "sks",
    
    # Community
    "event": "com",  # community
    "activity": "com",
    "group": "com",
    "volunteer": "com",
    
    # For Sale
    "clothing": "cla",  # clothing
    "shoes": "cla",
    "jewelry": "jwa",
    "books": "bks",  # books
    "music": "msg",  # musical instruments
    "guitar": "msg",
    "piano": "msg",
    "bike": "bia",  # bicycles
    "bicycle": "bia",
    "sports": "spo",  # sporting goods
    "fitness": "spo",
    "exercise": "spo",
    "outdoor": "spo",
    "camping": "spo",
    
    # Pets
    "pet": "pet",  # pets
    "dog": "pet",
    "cat": "pet",
    "puppy": "pet",
    "kitten": "pet",
    
    # General
    "general": "sss",  # general for sale
    "misc": "sss",
    "other": "sss"
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
    
    # Priority-based category detection (most specific first)
    priority_categories = [
        # Mobile devices (highest priority to avoid misclassification)
        ("iphone", "moa"), ("android", "moa"), ("smartphone", "moa"), ("mobile", "moa"),
        ("apple watch", "moa"), ("watch", "jwa"),
        
        # Electronics
        ("tv", "ele"), ("television", "ele"), ("camera", "ele"), ("gaming", "ele"),
        ("xbox", "ele"), ("playstation", "ele"), ("nintendo", "ele"), ("headphones", "ele"),
        
        # Computers
        ("laptop", "sys"), ("computer", "sys"), ("desktop", "sys"),
        
        # Vehicles
        ("car", "cta"), ("vehicle", "cta"), ("automobile", "cta"), ("truck", "cta"),
        ("motorcycle", "mca"), ("boat", "boa"), ("rv", "rva"),
        
        # Housing
        ("apartment", "apa"), ("rental", "apa"), ("house", "rea"), ("home", "rea"),
        ("condo", "rea"), ("room", "roo"), ("sublet", "roo"),
        
        # Furniture & Appliances
        ("furniture", "fua"), ("couch", "fua"), ("sofa", "fua"), ("table", "fua"),
        ("chair", "fua"), ("bed", "fua"), ("appliance", "fua"),
        
        # Jobs & Services
        ("job", "jjj"), ("employment", "jjj"), ("work", "jjj"), ("service", "sks"),
        ("repair", "sks"), ("cleaning", "sks"),
        
        # Other categories
        ("clothing", "cla"), ("shoes", "cla"), ("jewelry", "jwa"), ("books", "bks"),
        ("music", "msg"), ("guitar", "msg"), ("bike", "bia"), ("bicycle", "bia"),
        ("sports", "spo"), ("fitness", "spo"), ("pet", "pet"), ("dog", "pet"), ("cat", "pet")
    ]
    
    # Check priority categories first
    for category_name, category_code in priority_categories:
        if category_name in query_lower:
            return category_code
    
    # Fallback to full mapping
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
        system_prompt = """You are an expert Craigslist searcher with deep knowledge of Craigslist categories and search optimization. 

Extract from user request: 3-5 specific item recommendations, price range (min/max), and the MOST ACCURATE Craigslist category. Return JSON only:
{"recommendations": ["item1", "item2", "item3"], "min_price": null or number, "max_price": null or number, "category": "category_code", "explanation": "Brief explanation"}

CRITICAL: Choose the MOST SPECIFIC and ACCURATE category. Do NOT default to general categories unless absolutely necessary. ANY car brand and/or modelmentioned should be in the CTA category.

Craigslist Categories (use the most specific one):
- cta: Cars & trucks, vehicles, automotive
- mca: Motorcycles, scooters, ATVs
- boa: Boats, watercraft, marine
- rva: RVs, campers, trailers
- sys: Computers, laptops, desktops, tech
- moa: Mobile phones, smartphones, tablets, mobile devices, smartwatches, apple watches
- jwa: Jewelry, watches, luxury items
- ele: Electronics, TVs, cameras, gaming, audio
- fua: Furniture, home goods, appliances
- apa: Apartments, rentals, housing
- rea: Real estate, houses, condos, land
- roo: Rooms, sublets, shared housing
- jjj: Jobs, employment, careers
- sks: Skilled trades, services, repairs
- com: Community, events, activities
- cla: Clothing, shoes, fashion
- bks: Books, media, literature
- msg: Musical instruments, equipment
- bia: Bicycles, bikes, cycling
- spo: Sports, fitness, outdoor, recreation
- pet: Pets, animals, livestock
- sss: General for sale (ONLY if no specific category fits)

IMPORTANT: Mobile devices (iPhone, Android, etc.) go in 'moa', NOT 'cta'. Electronics go in 'ele'. Be precise with categories."""
        
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
