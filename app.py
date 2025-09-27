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
    """Extract zip code from user query with context awareness"""
    import re
    query_lower = query.lower()
    
    # Look for zip codes in specific contexts to avoid confusion with prices
    zip_patterns = [
        # "within X miles of 90210" - most specific
        r'within\s+\d+\s+miles?\s+of\s+(\d{5})',
        # "near 90210" or "around 90210"
        r'(?:near|around|in|at)\s+(\d{5})',
        # "zip code 90210" or "postal code 90210"
        r'(?:zip\s+code|postal\s+code)\s+(\d{5})',
        # "90210 area" or "90210 region"
        r'(\d{5})\s+(?:area|region|zone)',
        # General 5-digit pattern but validate it's a reasonable zip code
        r'\b(\d{5})\b'
    ]
    
    for pattern in zip_patterns:
        match = re.search(pattern, query_lower)
        if match:
            zip_code = match.group(1)
            # Validate it's a reasonable US zip code (10000-99999)
            if 10000 <= int(zip_code) <= 99999:
                return zip_code
    
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

def extract_price_from_query(query):
    """Extract price range from user query"""
    import re
    query_lower = query.lower()
    
    min_price = None
    max_price = None
    
    # Extract maximum price patterns with negative lookahead to avoid mileage confusion
    max_price_patterns = [
        r'under\s+\$?(\d{1,6})(?!\s*k?\s*miles?)',  # "under $15000" but not "under 100k miles"
        r'less\s+than\s+\$?(\d{1,6})(?!\s*k?\s*miles?)',  # "less than $15000" but not "less than 100k miles"
        r'max\s+price[:\s]+\$?(\d{1,6})',  # "max price: $15000"
        r'maximum\s+price[:\s]+\$?(\d{1,6})',  # "maximum price: $15000"
        r'budget[:\s]+\$?(\d{1,6})',  # "budget: $15000"
        r'(\d{1,6})\s+dollars?(?!\s*per\s*mile)',  # "15000 dollars" but not "100 dollars per mile"
        r'\$(\d{1,6})',  # "$15000" - dollar sign is clear indicator
        r'price[:\s]+\$?(\d{1,6})',  # "price: $15000"
        r'cost[:\s]+\$?(\d{1,6})'  # "cost: $15000"
    ]
    
    for pattern in max_price_patterns:
        match = re.search(pattern, query_lower)
        if match:
            price = int(match.group(1))
            # Additional validation: check if this looks like mileage, not price
            price_text = match.group(0).lower()
            if 'k' in price_text and ('mile' in price_text or 'mi' in price_text):
                continue  # Skip this match, it's likely mileage
            # Validate it's a reasonable price (not a zip code)
            if 100 <= price <= 999999:  # Reasonable price range
                max_price = price
                break
    
    # Extract minimum price patterns with negative lookahead to avoid mileage confusion
    min_price_patterns = [
        r'over\s+\$?(\d{1,6})(?!\s*k?\s*miles?)',  # "over $10000" but not "over 100k miles"
        r'more\s+than\s+\$?(\d{1,6})(?!\s*k?\s*miles?)',  # "more than $10000" but not "more than 100k miles"
        r'min\s+price[:\s]+\$?(\d{1,6})',  # "min price: $10000"
        r'minimum\s+price[:\s]+\$?(\d{1,6})',  # "minimum price: $10000"
        r'starting\s+at\s+\$?(\d{1,6})',  # "starting at $10000"
        r'from\s+\$?(\d{1,6})(?!\s*k?\s*miles?)'  # "from $10000" but not "from 100k miles"
    ]
    
    for pattern in min_price_patterns:
        match = re.search(pattern, query_lower)
        if match:
            price = int(match.group(1))
            # Additional validation: check if this looks like mileage, not price
            price_text = match.group(0).lower()
            if 'k' in price_text and ('mile' in price_text or 'mi' in price_text):
                continue  # Skip this match, it's likely mileage
            # Validate it's a reasonable price (not a zip code)
            if 100 <= price <= 999999:  # Reasonable price range
                min_price = price
                break
    
    return min_price, max_price

def extract_vehicle_parameters(query):
    """Extract vehicle-specific parameters from user query"""
    import re
    query_lower = query.lower()
    
    params = {
        'search_titles_only': False,
        'hide_duplicates': False,
        'min_year': None,
        'max_year': None,
        'min_miles': None,
        'max_miles': None,
        'drive_type': None,
        'transmission': None,
        'body_type': None,
        'cylinders': None,
        'fuel_type': None,
        'paint_color': None,
        'title_status': None
    }
    
    # Search titles only
    if any(phrase in query_lower for phrase in ['title only', 'titles only', 'search titles']):
        params['search_titles_only'] = True
    
    # Hide duplicates
    if any(phrase in query_lower for phrase in ['hide duplicates', 'no duplicates', 'unique only']):
        params['hide_duplicates'] = True
    
    # Model year range
    year_patterns = [
        (r'(\d{4})\s*to\s*(\d{4})', 'range'),  # "2010 to 2015"
        (r'(\d{4})\s*-\s*(\d{4})', 'range'),   # "2010-2015"
        (r'after\s*(\d{4})', 'min'),           # "after 2010"
        (r'before\s*(\d{4})', 'max'),          # "before 2015"
        (r'from\s*(\d{4})', 'min'),            # "from 2010"
        (r'(\d{4})\s*or\s*newer', 'min'),      # "2010 or newer"
        (r'(\d{4})\s*or\s*older', 'max'),      # "2015 or older"
        (r'(\d{4})s?', 'single')               # "2010s" or "2010"
    ]
    
    for pattern, match_type in year_patterns:
        match = re.search(pattern, query_lower)
        if match:
            if match_type == 'range':
                params['min_year'] = int(match.group(1))
                params['max_year'] = int(match.group(2))
            elif match_type == 'min':
                params['min_year'] = int(match.group(1))
            elif match_type == 'max':
                params['max_year'] = int(match.group(1))
            elif match_type == 'single':
                year = int(match.group(1))
                if 1990 <= year <= 2025:  # Reasonable year range
                    params['min_year'] = year
            break
    
    # Mileage range
    mileage_patterns = [
        (r'(\d+)\s*to\s*(\d+)\s*miles?', 'range'),     # "50k to 100k miles"
        (r'(\d+)\s*-\s*(\d+)\s*miles?', 'range'),      # "50k-100k miles"
        (r'under\s*(\d+)\s*miles?', 'max'),            # "under 100k miles"
        (r'over\s*(\d+)\s*miles?', 'min'),             # "over 50k miles"
        (r'less\s+than\s*(\d+)\s*miles?', 'max'),      # "less than 100k miles"
        (r'more\s+than\s*(\d+)\s*miles?', 'min'),      # "more than 50k miles"
        (r'(\d+)k\s*miles?', 'single')                 # "75k miles"
    ]
    
    for pattern, match_type in mileage_patterns:
        match = re.search(pattern, query_lower)
        if match:
            if match_type == 'range':
                params['min_miles'] = int(match.group(1)) * 1000
                params['max_miles'] = int(match.group(2)) * 1000
            elif match_type == 'min':
                params['min_miles'] = int(match.group(1)) * 1000
            elif match_type == 'max':
                params['max_miles'] = int(match.group(1)) * 1000
            elif match_type == 'single':
                params['max_miles'] = int(match.group(1)) * 1000
            break
    
    # Drive type
    drive_mapping = {
        'fwd': 1, 'front wheel drive': 1, 'front-wheel drive': 1,
        'rwd': 2, 'rear wheel drive': 2, 'rear-wheel drive': 2,
        'awd': 3, 'all wheel drive': 3, 'all-wheel drive': 3,
        '4wd': 4, 'four wheel drive': 4, '4 wheel drive': 4
    }
    
    for term, code in drive_mapping.items():
        if term in query_lower:
            params['drive_type'] = code
            break
    
    # Transmission
    if 'manual' in query_lower and 'automatic' not in query_lower:
        params['transmission'] = 1
    elif 'automatic' in query_lower and 'manual' not in query_lower:
        params['transmission'] = 2
    
    # Body type
    body_mapping = {
        'sedan': 3, 'suv': 8, 'truck': 1, 'coupe': 2, 'convertible': 4,
        'wagon': 5, 'hatchback': 6, 'van': 7, 'pickup': 1
    }
    
    for term, code in body_mapping.items():
        if term in query_lower:
            params['body_type'] = code
            break
    
    # Cylinders
    cylinder_patterns = [
        (r'(\d+)\s*cylinder', 'single'),
        (r'(\d+)\s*cyl', 'single'),
        (r'v(\d+)', 'single')
    ]
    
    for pattern, match_type in cylinder_patterns:
        match = re.search(pattern, query_lower)
        if match:
            params['cylinders'] = int(match.group(1))
            break
    
    # Fuel type
    fuel_mapping = {
        'gas': 1, 'gasoline': 1, 'petrol': 1,
        'diesel': 2,
        'hybrid': 3,
        'electric': 4, 'ev': 4
    }
    
    for term, code in fuel_mapping.items():
        if term in query_lower:
            params['fuel_type'] = code
            break
    
    # Paint color
    color_mapping = {
            'black': 1,
            'blue': 2,
            'brown': 3,
            'green': 4,
            'grey': 5,
            'gray': 5,   
            'orange': 6,
            'purple': 7,
            'red': 8,
            'white': 9,
            'silver': 10,
            'yellow': 11,
            'custom': 20
    }
    
    for term, code in color_mapping.items():
        if term in query_lower:
            params['paint_color'] = code
            break
    
    # Title status
    title_mapping = {
        'clean': 1, 'clean title': 1,
        'salvage': 2, 'salvage title': 2,
        'rebuilt': 3, 'rebuilt title': 3,
        'parts only': 4, 'parts': 4,
        'missing': 5, 'missing title': 5
    }
    
    for term, code in title_mapping.items():
        if term in query_lower:
            params['title_status'] = code
            break
    
    return params

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
    
        # Extract price information with better patterns and negative lookahead
        price_patterns = [
            r'under\s+\$?(\d{1,6})(?!\s*k?\s*miles?)',  # "under $15000" but not "under 100k miles"
            r'less\s+than\s+\$?(\d{1,6})(?!\s*k?\s*miles?)',  # "less than $15000" but not "less than 100k miles"
            r'max\s+price[:\s]+\$?(\d{1,6})',  # "max price: $15000"
            r'maximum\s+price[:\s]+\$?(\d{1,6})',  # "maximum price: $15000"
            r'budget[:\s]+\$?(\d{1,6})',  # "budget: $15000"
            r'(\d{1,6})\s+dollars?(?!\s*per\s*mile)',  # "15000 dollars" but not "100 dollars per mile"
            r'\$(\d{1,6})',  # "$15000" - dollar sign is clear indicator
            r'price[:\s]+\$?(\d{1,6})',  # "price: $15000"
            r'cost[:\s]+\$?(\d{1,6})'  # "cost: $15000"
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, ai_response, re.IGNORECASE)
            if match:
                price = int(match.group(1))
                # Validate it's a reasonable price (not a zip code)
                if 100 <= price <= 999999:  # Reasonable price range
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

def generate_craigslist_link(keywords, city, category, min_price=None, max_price=None, zip_code=None, radius=None, vehicle_params=None):
    """Generate a Craigslist search URL with zip code, radius, and vehicle-specific parameters support"""
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
    
    # Add vehicle-specific parameters if provided
    if vehicle_params:
        # Search options
        if vehicle_params.get('search_titles_only'):
            params.append("srchType=T")
        if vehicle_params.get('hide_duplicates'):
            params.append("bundleDuplicates=1")
        
        # Vehicle parameters (only for cars & trucks category)
        if category == 'cta':
            if vehicle_params.get('min_year'):
                params.append(f"min_auto_year={vehicle_params['min_year']}")
            if vehicle_params.get('max_year'):
                params.append(f"max_auto_year={vehicle_params['max_year']}")
            if vehicle_params.get('min_miles'):
                params.append(f"min_auto_miles={vehicle_params['min_miles']}")
            if vehicle_params.get('max_miles'):
                params.append(f"max_auto_miles={vehicle_params['max_miles']}")
            if vehicle_params.get('drive_type'):
                params.append(f"auto_drivetrain={vehicle_params['drive_type']}")
            if vehicle_params.get('transmission'):
                params.append(f"auto_transmission={vehicle_params['transmission']}")
            if vehicle_params.get('body_type'):
                params.append(f"auto_bodytype={vehicle_params['body_type']}")
            if vehicle_params.get('cylinders'):
                params.append(f"auto_cylinders={vehicle_params['cylinders']}")
            if vehicle_params.get('fuel_type'):
                params.append(f"auto_fuel_type={vehicle_params['fuel_type']}")
            if vehicle_params.get('paint_color'):
                params.append(f"auto_paint={vehicle_params['paint_color']}")
            if vehicle_params.get('title_status'):
                params.append(f"auto_title_status={vehicle_params['title_status']}")
    
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
        
        # Extract city, category, zip code, radius, price, and vehicle parameters from query
        city = extract_city_from_query(user_query)
        category = extract_category_from_query(user_query)
        zip_code = extract_zip_code_from_query(user_query)
        radius = extract_radius_from_query(user_query)
        vehicle_params = extract_vehicle_parameters(user_query)
        
        # Extract price information from query
        min_price, max_price = extract_price_from_query(user_query)
        
        # Prepare prompt for Ollama Mistral 7B
        system_prompt = """You are an expert Craigslist searcher. Extract from user request: 3-5 specific item recommendations, price range (min/max), different parameters, and the MOST ACCURATE Craigslist category. Return JSON only:

{"recommendations": ["item1", "item2", "item3"], "min_price": null or number, "max_price": null or number, "category": "category_code", "explanation": "Brief explanation"}

CRITICAL RULES:
1. Choose the MOST SPECIFIC category. Do NOT default to general categories.
2. For vehicle searches, ONLY include the core vehicle name/model in recommendations - NOT color, year, mileage, transmission, or title status.
3. Vehicle-specific details (color, year, mileage, transmission, title status) are handled by URL parameters, not search keywords.
4. Do not include search terms like "refurbished", "used" or "second hand" in the search query.
5. ABSOLUTELY NO UNDERSCORES IN THE SEARCH QUERY.
6. CRITICAL: When extracting prices, be VERY careful to distinguish between:
   - PRICES: "under $15000", "less than $1000", "$5000"
   - ZIP CODES: "90210", "10001", "94102"
   - NEVER confuse prices with zip codes in your analysis!
7. CRITICAL: If the user DOES NOT specify a price, DO NOT PUT PRICE PARAMETERS IN THE JSON.
8. CRITICAL: NEVER extract mileage as price. "100k miles" is MILEAGE, not "$100". Only extract prices when there are clear price indicators like "$", "under", "budget", "price", "cost".
9. CRITICAL: IF the user does not specify a specific car/item (such as "fun manual cars") give valid inferences based on the user's query (such as, if the user asks for "fun manual cars" give suggestions you think are valid like BMW 335i, corvette, etc.), but do NOT search "fun manual cars" as the search query.
10. CRITICAL: When the user specifies vehicle-specific details (such as white color) make sure to KEEP THE COLOR IN THE URL PARAMETER EXACTLY AS THE USER SPECIFIES, IF THE USER SPECIFIES.
11. DO NOT DEFAULT TO A RANDOM COLOR (such as blue) IN THE URL PARAMETERS IF THE USER DOES NOT SPECIFY A COLOR. MAKE SURE TO ABSOLUTELY FOLLOW THE USER'S SPECIFICATIONS AT ALL COSTS.
EXAMPLES:
- Query: "black BMW 335i 2010 to 2015 under 100k miles automatic clean title"
- CORRECT: {"recommendations": ["BMW 335i", "BMW 3 Series", "BMW 335i Sedan"], "category": "cta"}
- WRONG: {"recommendations": ["black BMW 335i", "2010-2015", "automatic", "clean title"]}

- Query: "Honda Civic 2015 or newer automatic FWD clean title under $15000 within 15 miles of 90210"
- CORRECT: {"recommendations": ["Honda Civic", "Honda Civic Sedan", "Honda Civic Coupe"], "max_price": 15000, "category": "cta"}
- WRONG: {"recommendations": ["Honda Civic 2015", "automatic", "FWD", "clean title"], "max_price": 90210}

- Query: "MacBook Pro 13 inch under $1000"
- CORRECT: {"recommendations": ["MacBook Pro", "MacBook Pro 13", "MacBook Pro 13 inch"], "max_price": 1000, "category": "sys"}
- WRONG: {"recommendations": ["MacBook Pro 13 inch under $1000"]}

- Query: "BMW 335i 2010 to 2015 under 100k miles automatic clean title"
- CORRECT: {"recommendations": ["BMW 335i", "BMW 3 Series", "BMW 335i Sedan"], "category": "cta"}
- WRONG: {"recommendations": ["BMW 335i", "BMW 3 Series"], "max_price": 100, "category": "cta"}

- Query: "white bmw i3 within 100 miles of 94086 under 100k miles clean title"
- CORRECT: Proper recomendation with THE COLOR WHITE IN THE URL PARAMETER: https://sfbay.craigslist.org/search/cta?auto_paint=9&auto_title_status=1&max_auto_miles=100000&postal=94086&query=BMW%20i3&search_distance=100#search=2~gallery~0
- WRONG: Proper recommendation with the color blue in the URL parameter, which is NOT what the user specified:https://sfbay.craigslist.org/search/cta?auto_paint=2&auto_title_status=1&max_auto_miles=100000&postal=94086&query=BMW%20i3&search_distance=100#search=2~gallery~0



PRICE vs ZIP CODE vs MILEAGE DISTINCTION:
- PRICES: Look for "$" symbol, "under", "less than", "budget", "price", "cost"
- ZIP CODES: Look for "within X miles of", "near", "around", "zip code", "postal code"
- MILEAGE: Look for "k miles", "miles", "mi" - NEVER extract as price
- NEVER extract a 5-digit number as price if it appears after "miles of" or "near"
- NEVER extract "100k miles" as "$100" - it's MILEAGE, not PRICE

Key Categories:
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
                    parsed_response.get("min_price") or min_price,  # Use extracted price or AI price
                    parsed_response.get("max_price") or max_price,  # Use extracted price or AI price
                    zip_code,  # Include zip code
                    radius,    # Include radius
                    vehicle_params  # Include vehicle parameters
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
            "radius": radius,
            "vehicle_params": vehicle_params  # Include vehicle parameters
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
