# AI Craigslist Link Generator Bot

An intelligent web application that uses local running models provided by Ollama (tested via Mistral 7b) to understand user intent and generate optimized Craigslist search links. Simply describe what you're looking for in natural language, and the AI will create the perfect search query with relevant keywords and filters.

## ✨ Features

- **Natural Language Processing**: Describe what you want in plain English
- **AI-Powered Recommendations**: Ollama Mistral 7B (local, free) suggests relevant items and brands
- **Smart Category Detection**: Automatically identifies the best Craigslist category
- **City/Region Support**: Works with multiple Craigslist regions
- **Price Filtering**: Automatically extracts and applies price ranges
- **Modern UI**: Clean, responsive design with smooth animations
- **Example Queries**: Click-to-try example searches

## 🚀 Quick Start

### Prerequisites

- Python 3.7 or higher
- Ollama installed locally ([Download here](https://ollama.ai/))

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

## 📖 Usage Examples

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

## 🏗️ Architecture

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

### Key Components
- **Query Processing**: Analyzes user input for intent
- **Category Mapping**: Maps common terms to Craigslist categories
- **City Detection**: Identifies mentioned cities/regions
- **Price Extraction**: Parses budget constraints
- **Link Building**: Constructs search URLs with proper parameters

## 🔧 Configuration

### Supported Cities
The application supports major Craigslist regions and all valid zip codes within CraigsList:
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

### Supported Categories
- **cta**: Cars & Trucks
- **sys**: Computers
- **fua**: Furniture
- **apa**: Apartments
- **rea**: Real Estate
- **jjj**: Jobs
- **sss**: General Search

## 🚀 Deployment

### Local Development
```bash
python app.py
```

### Production with Gunicorn
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Docker (Optional)
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

## 🔒 Security Notes

- **API Keys**: Never commit your `.env` file to version control
- **Rate Limiting**: Consider implementing rate limiting for production use
- **Input Validation**: All user inputs are sanitized and validated

## 🧪 Testing

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

**Built using Flask, Ollama Mistral 7B (local, free), and modern web technologies**
