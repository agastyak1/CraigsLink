# CraigsLink - easily surf Craigslist utilizing natural language prompts

An intelligent web application that uses OpenAI's GPT to understand user intent and generate optimized Craigslist search links. Simply describe what you're looking for in natural language, and the AI will create the perfect search query with relevant keywords and filters. 

## Features

- **Natural Language Processing**: Describe what you want in plain English
- **AI-Powered Recommendations**: Ollama Mistral 7B (local, free) suggests relevant items and brands
- **Smart Category Detection**: Automatically identifies the best Craigslist category
- **City/Region Support**: Works with multiple Craigslist regions
- **Price Filtering**: Automatically extracts and applies price ranges
- **Modern UI**: Clean, responsive design with smooth animations
- **Example Queries**: Click-to-try example searches
## Application Examples
![CraigsLink Dark](https://github.com/agastyak1/CraigsLink/raw/8dac487eca31908cb65d953b3242efc7c5a51b0c/craigsLinkResults/craigslinkDark.png)
![CraigsLink Light](https://github.com/agastyak1/CraigsLink/raw/8dac487eca31908cb65d953b3242efc7c5a51b0c/craigsLinkResults/craigslinkLight.png)
![CraigsLink Processing](https://github.com/agastyak1/CraigsLink/raw/8dac487eca31908cb65d953b3242efc7c5a51b0c/craigsLinkResults/craigslinkProcessing.png)
![CraigsLink Results](https://github.com/agastyak1/CraigsLink/blob/8dac487eca31908cb65d953b3242efc7c5a51b0c/craigsLinkResults/craigslinkResults.png?raw=true)
## Quick Start

### Prerequisites

- Python 3.7 or higher
- Ollama installed locally ([Download here](https://ollama.ai/))
- Mistral 7B model has been tested as a balance between speed and accuracy; however, higher parameter models may work better depending on your processing power

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd CraigsLink
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp env.example .env
   ```
   
   Edit `.env` if you want to customize Ollama settings:
   ```bash
   OLLAMA_BASE_URL=http://localhost:11434
   OLLAMA_MODEL=mistral:7b
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Open your browser**
   Navigate to `http://localhost:5000`

## Usage Examples

### Example 1: Car Search
**Input**: "I want a reliable car under $10,000"

**Output**: 
- **Recommendations**: Honda Civic, Toyota Corolla, Mazda3
- **Link**: `https://sfbay.craigslist.org/search/cta?query=honda+civic|toyota+corolla|mazda3&max_price=10000`

### Example 2: Laptop Search
**Input**: "cheap laptop for coding under $500"

**Output**:
- **Recommendations**: Dell XPS, Lenovo ThinkPad, MacBook Air
- **Link**: `https://sfbay.craigslist.org/search/sys?query=dell+xps|lenovo+thinkpad|macbook+air&max_price=500`

### Example 3: Furniture Search
**Input**: "furniture for small apartment in NYC"

**Output**:
- **Recommendations**: IKEA furniture, compact sofa, small dining table
- **Link**: `https://nyc.craigslist.org/search/fua?query=ikea+furniture|compact+sofa|small+dining+table`

## Architecture

### Backend (Python/Flask)
- **Flask**: Web framework for API endpoints
- **Ollama Mistral 7B**: Natural language processing and recommendations (local, free)
- **Smart Parsing**: Extracts keywords, prices, and categories
- **URL Generation**: Creates optimized Craigslist search links

### Frontend (Vanilla JavaScript)
- **Modern UI**: Clean, responsive design
- **Interactive Elements**: Example tags, loading states, error handling
- **Accessibility**: ARIA labels, keyboard shortcuts
- **Responsive Design**: Works on all device sizes
- **Dark and Light Mode**: Appealing design with light/dark toggles

### Key Components
- **Query Processing**: Analyzes user input for intent
- **Category Mapping**: Maps common terms to Craigslist categories
- **City Detection**: Identifies mentioned cities/regions
- **Price Extraction**: Parses budget constraints
- **Link Building**: Constructs search URLs with proper parameters

## 🔧 Configuration

### Supported Cities
The application supports major Craigslist regions (and all zip codes) :
- San Francisco Bay Area (default)
- New York City
- Los Angeles
- Chicago
- Seattle
- Austin
- Denver
- Miami
- Atlanta
- Phoenix
- Dallas
- Houston

### Supported Categories - almost all!
- **cta**: Cars & Trucks
- **sys**: Computers
- **fua**: Furniture
- **apa**: Apartments
- **rea**: Real Estate
- **jjj**: Jobs
- **sss**: General Search
- Almost ALL categories in Craigslist are supported - the above are just some common/general ones.

### Manual Testing
1. Start the application
2. Try various example queries
3. Test with different cities and categories
4. Verify generated links work correctly

### API Testing
```bash
curl -X POST http://localhost:5000/api/generate-link \
  -H "Content-Type: application/json" \
  -d '{"query": "reliable car under $10,000"}'
```

## 🔮 Future Enhancements

- [ ] **City Selection Dropdown**: User-selectable city/region
- [ ] **IP Geolocation**: Auto-detect user's city
- [ ] **Multiple Marketplaces**: Support for Facebook Marketplace, OfferUp
- [ ] **User Accounts**: Save and manage search history
- [ ] **Browser Extension**: Chrome/Firefox extension version
- [ ] **Advanced Filters**: Condition, mileage, year ranges
- [ ] **Search Analytics**: Track popular searches and trends

## 📝 License

This project is open source and available under the [MIT License](LICENSE).

**Built using Flask, Ollama Mistral 7B (local, free), Python, JS, and HTML/CSS**
