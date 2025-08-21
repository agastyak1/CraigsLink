#!/bin/bash

# AI Craigslist Link Generator - Startup Script

echo "🚀 Starting AI Craigslist Link Generator..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.7 or higher."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from template..."
    cp env.example .env
    echo "📝 Please edit .env file and add your OpenAI API key:"
    echo "   OPENAI_API_KEY=your_actual_api_key_here"
    echo ""
    echo "🔑 Get your API key from: https://platform.openai.com/api-keys"
    echo ""
    read -p "Press Enter after you've added your API key..."
fi

# Check if requirements are installed
if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
    echo "📦 Installing dependencies..."
    pip3 install -r requirements.txt
fi

# Start the application
echo "🌟 Starting Flask application..."
echo "🌐 Open your browser to: http://localhost:5000"
echo "⏹️  Press Ctrl+C to stop the application"
echo ""

python3 app.py
