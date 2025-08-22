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
    "apple watch": "ele",
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
        ("apple watch", "ele"), ("watch", "jwa"),
        
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

def extract_partial_response(ai_response, fallback_category):
    """Intelligently extract information from AI response when JSON parsing fails"""
    import re
    
    # Initialize with fallback values
    result = {
        "recommendations": [],
        "min_price": None,
        "max_price": None,
        "category": fallback_category or "sss",
        "explanation": ai_response
    }
    
    # Try to extract recommendations from the response text
    # Look for patterns like "recommended monitors are:", "items:", etc.
    recommendation_patterns = [
        r'recommendations?[:\s]+([^.]+)',
        r'items?[:\s]+([^.]+)',
        r'suggested[:\s]+([^.]+)',
        r'popular[:\s]+([^.]+)',
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z0-9]+)*\s+(?:monitor|tv|laptop|car|phone|furniture|apartment|house|job))',
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z0-9]+)*\s+[A-Z][a-z]+(?:\s+[A-Z][a-z0-9]+)*)'
    ]
    
    for pattern in recommendation_patterns:
        matches = re.findall(pattern, ai_response, re.IGNORECASE)
        if matches:
            # Clean up the matches and extract individual items
            for match in matches:
                # Split by common separators
                items = re.split(r'[,|;]|\sand\s', match.strip())
                for item in items:
                    item = item.strip()
                    if item and len(item) > 2 and item not in result["recommendations"]:
                        result["recommendations"].append(item)
            
            if result["recommendations"]:
                break
    
    # If no recommendations found, try to extract from the explanation
    if not result["recommendations"]:
        # Look for brand names and product types
        brand_patterns = [
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z0-9]+)*\s+(?:monitor|tv|laptop|car|phone|furniture|apartment|house|job))',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z0-9]+)*\s+[A-Z][a-z]+(?:\s+[A-Z][a-z0-9]+)*)'
        ]
        
        for pattern in brand_patterns:
            matches = re.findall(pattern, ai_response)
            if matches:
                for match in matches:
                    if match and len(match) > 2 and match not in result["recommendations"]:
                        result["recommendations"].append(match)
                break
    
    # Extract price information
    price_patterns = [
        r'under\s+\$?(\d+)',
        r'less\s+than\s+\$?(\d+)',
        r'max\s+price[:\s]+\$?(\d+)',
        r'maximum\s+price[:\s]+\$?(\d+)',
        r'budget[:\s]+\$?(\d+)',
        r'(\d+)\s+dollars?',
        r'\$(\d+)'
    ]
    
    for pattern in price_patterns:
        match = re.search(pattern, ai_response, re.IGNORECASE)
        if match:
            price = int(match.group(1))
            if result["max_price"] is None or price < result["max_price"]:
                result["max_price"] = price
            break
    
    # Extract minimum price if mentioned
    min_price_patterns = [
        r'over\s+\$?(\d+)',
        r'more\s+than\s+\$?(\d+)',
        r'min\s+price[:\s]+\$?(\d+)',
        r'minimum\s+price[:\s]+\$?(\d+)',
        r'starting\s+at\s+\$?(\d+)'
    ]
    
    for pattern in min_price_patterns:
        match = re.search(pattern, ai_response, re.IGNORECASE)
        if match:
            result["min_price"] = int(match.group(1))
            break
    
    # If still no recommendations, provide generic ones based on category
    if not result["recommendations"]:
        if fallback_category == "sys":
            result["recommendations"] = ["Computer", "Laptop", "Monitor", "Desktop", "Tablet"]
        elif fallback_category == "cta":
            result["recommendations"] = ["Car", "Truck", "SUV", "Sedan", "Vehicle"]
        elif fallback_category == "fua":
            result["recommendations"] = ["Furniture", "Couch", "Table", "Chair", "Bed"]
        elif fallback_category == "apa":
            result["recommendations"] = ["Apartment", "Studio", "1BR", "2BR", "Rental"]
        else:
            result["recommendations"] = ["Item", "Product", "Service", "Goods"]
    
    return result

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
        system_prompt = """You are an expert Craigslist searcher. Extract from user request: 3-5 specific item recommendations, price range (min/max), and the MOST ACCURATE Craigslist category. Return JSON only:

{"recommendations": ["item1", "item2", "item3"], "min_price": null or number, "max_price": null or number, "category": "category_code", "explanation": "Brief explanation"}
CRITICAL: Do not include search terms like "refurbished","used" or "second hand" in the search query.
CRITICAL: ABSOLUTELY NO UNDERSCORES IN THE SEARCH QUERY.
CRITICAL: Choose the MOST SPECIFIC category. Do NOT default to general categories. Do NOT provide underscores within the search query (example: do NOT write "software_jobs," instead write "software jobs").
CRITICAL: Laptops, desktops, computers, and tech go in 'sys', NOT 'ele'.
ABSOLUTELY NO UNDERSCORES IN THE SEARCH QUERY.
- cta: Cars & trucks, vehicles, automotive
- mca: Motorcycles, scooters, ATVs
- boa: Boats, watercraft, marine
- rva: RVs, campers, trailers
- sys: Computers, laptops, desktops, tech
- moa: Mobile phones, smartphones, tablets
- jwa: Jewelry, watches, luxury items
- ele: Electronics, smartwatches, TVs, cameras, gaming, audio
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

IMPORTANT: Mobile devices go in 'moa', NOT 'cta'. Electronics go in 'ele'. Be precise."""
        
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
                "num_predict": 1000,  # Increased for complete responses
                "top_k": 15,         # Limit token selection for speed
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
            
            # Log the response for debugging (remove in production)
            print(f"Ollama response length: {len(ai_response)}")
            print(f"Ollama response preview: {ai_response[:200]}...")
            
        except requests.exceptions.Timeout:
            raise Exception("Request timed out. Ollama model is still processing. Try again in a moment.")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Ollama API error: {str(e)}")
        except KeyError as e:
            raise Exception(f"Invalid response from Ollama: {str(e)}")
        
        # Try to extract JSON from response with improved parsing
        try:
            # First, try to find complete JSON in the response
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', ai_response, re.DOTALL)
            if json_match:
                try:
                    parsed_response = json.loads(json_match.group())
                except json.JSONDecodeError:
                    # Try to fix common JSON issues
                    fixed_json = json_match.group()
                    # Remove trailing incomplete text
                    if fixed_json.count('{') > fixed_json.count('}'):
                        # Find the last complete object
                        last_brace = fixed_json.rfind('}')
                        if last_brace > 0:
                            fixed_json = fixed_json[:last_brace + 1]
                    
                    try:
                        parsed_response = json.loads(fixed_json)
                    except json.JSONDecodeError:
                        raise Exception("JSON parsing failed after cleanup")
            else:
                # Try to extract partial information from the response
                parsed_response = extract_partial_response(ai_response, category)
                
        except Exception as e:
            # Intelligent fallback based on the actual response content
            parsed_response = extract_partial_response(ai_response, category)
        
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
