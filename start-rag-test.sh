#!/bin/bash

# SmartBin RAG Agent Testing Environment Startup Script

echo "🧠 Starting SmartBin RAG Agent Testing Environment"
echo "=================================================="

# Check if Google API key is set
if [ -z "$GOOGLE_API_KEY" ]; then
    echo "❌ GOOGLE_API_KEY environment variable not set!"
    echo "Please set it first:"
    echo "  export GOOGLE_API_KEY=your_google_api_key_here"
    echo ""
    echo "You can get a key from: https://makersuite.google.com/app/apikey"
    exit 1
fi

echo "✅ Google API key is configured"

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Please run this script from the project root directory"
    exit 1
fi

# Install Python dependencies if needed
echo "📦 Checking Python dependencies..."
cd backend
if ! python -c "import langchain, langgraph, chromadb, langchain_google_genai" 2>/dev/null; then
    echo "Installing RAG dependencies..."
    pip install langchain langgraph chromadb langchain-google-genai
else
    echo "✅ RAG dependencies are already installed"
fi

# Test the RAG agent
echo "🧪 Testing RAG agent..."
python test_rag.py

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 RAG agent is working correctly!"
    echo ""
    echo "🚀 Starting FastAPI server..."
    echo "   Backend will be available at: http://localhost:8000"
    echo "   RAG endpoints:"
    echo "   - Health check: http://localhost:8000/rag/health"
    echo "   - Query: POST http://localhost:8000/rag/query"
    echo ""
    echo "🌐 To test the frontend:"
    echo "   1. Open rag-test-frontend/index.html in your browser"
    echo "   2. Set API URL to: http://localhost:8000"
    echo "   3. Try the sample questions!"
    echo ""
    echo "Press Ctrl+C to stop the server"
    echo ""
    
    # Start the FastAPI server
    uvicorn src.backend.main:app --reload --host 0.0.0.0 --port 8000
else
    echo "❌ RAG agent test failed. Please check the errors above."
    exit 1
fi
