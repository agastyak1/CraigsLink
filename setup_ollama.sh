#!/bin/bash

# Ollama Setup Script for AI Craigslist Link Generator

echo "🚀 Setting up Ollama for AI Craigslist Link Generator..."
echo "=================================================="

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "❌ Ollama is not running. Please start Ollama first:"
    echo "   ollama serve"
    echo ""
    echo "   Or if you haven't installed Ollama yet:"
    echo "   Visit: https://ollama.ai/download"
    exit 1
fi

echo "✅ Ollama is running on localhost:11434"
echo ""

# Check if Mistral model is already downloaded
if ollama list | grep -q "mistral:7b"; then
    echo "✅ Mistral 7B model is already downloaded"
else
    echo "📥 Downloading Mistral 7B model (this may take a few minutes)..."
    echo "   Model size: ~4GB"
    echo ""
    ollama pull mistral:7b
    echo ""
    echo "✅ Mistral 7B model downloaded successfully!"
fi

echo ""
echo "🧪 Testing the model..."
echo "Testing with: 'Hello, can you help me find a car?'"
echo ""

# Test the model
test_response=$(ollama run mistral:7b "Hello, can you help me find a car?" 2>/dev/null | head -3)

if [ $? -eq 0 ]; then
    echo "✅ Model test successful!"
    echo "Sample response: ${test_response}"
else
    echo "❌ Model test failed. Please check Ollama installation."
    exit 1
fi

echo ""
echo "🎉 Ollama setup complete!"
echo ""
echo "Next steps:"
echo "1. Make sure your .env file has:"
echo "   OLLAMA_BASE_URL=http://localhost:11434"
echo "   OLLAMA_MODEL=mistral:7b"
echo ""
echo "2. Start the Flask application:"
echo "   python3 app.py"
echo ""
echo "3. Open your browser to: http://localhost:5000"
echo ""
echo "The application will now use your local Ollama model for free!"
