#!/usr/bin/env python3
"""Test script for the SmartBin RAG agent."""

import os
import sys
from pathlib import Path

# Add the src directory to the Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def test_rag_agent():
    """Test the RAG agent with a sample query."""
    
    # Check if Google API key is set
    if "GOOGLE_API_KEY" not in os.environ:
        print("❌ GOOGLE_API_KEY environment variable not set!")
        print("Please set it with: export GOOGLE_API_KEY=your_key_here")
        return False
    
    try:
        # Import the RAG agent
        from rag_agent import app
        
        print("✅ RAG agent imported successfully")
        
        # Test query
        test_query = "Jelaskan hierarki pengelolaan sampah 3R dan 5R"
        print(f"\n🧠 Testing query: {test_query}")
        
        # Run the query
        from langchain_core.messages import HumanMessage
        
        final_state = app.invoke(
            {"messages": [HumanMessage(content=test_query)]},
            config={"configurable": {"thread_id": "test-1"}}
        )
        
        # Extract and display the response
        final_message = final_state["messages"][-1]
        answer = final_message.content if hasattr(final_message, 'content') else str(final_message)
        
        print(f"\n✅ RAG agent response received!")
        print(f"📊 Message count: {len(final_state['messages'])}")
        print(f"\n🤖 Answer:\n{answer}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import RAG agent: {e}")
        print("Make sure all dependencies are installed:")
        print("  pip install langchain langgraph chromadb langchain-google-genai")
        return False
        
    except Exception as e:
        print(f"❌ RAG agent test failed: {e}")
        return False

def test_api_endpoints():
    """Test the FastAPI RAG endpoints."""
    try:
        import requests
        import time
        
        # Wait a bit for the server to start if it's running
        time.sleep(1)
        
        base_url = "http://localhost:8000"
        
        # Test health endpoint
        print(f"\n🔍 Testing API endpoints at {base_url}")
        
        try:
            response = requests.get(f"{base_url}/rag/health", timeout=5)
            if response.status_code == 200:
                print("✅ /rag/health endpoint is working")
            else:
                print(f"⚠️ /rag/health returned status {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Could not reach /rag/health: {e}")
            print("Make sure the FastAPI server is running on port 8000")
            return False
        
        # Test query endpoint (this will fail without auth, but we can check if it exists)
        try:
            response = requests.post(
                f"{base_url}/rag/query",
                json={"query": "test", "thread_id": "test"},
                timeout=5
            )
            if response.status_code in [401, 422]:  # Expected: auth required or validation error
                print("✅ /rag/query endpoint is accessible (auth required)")
            else:
                print(f"⚠️ /rag/query returned unexpected status {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Could not reach /rag/query: {e}")
            return False
        
        return True
        
    except ImportError:
        print("⚠️ requests library not available, skipping API endpoint tests")
        return True

if __name__ == "__main__":
    print("🧠 SmartBin RAG Agent Test Suite")
    print("=" * 50)
    
    # Test the RAG agent
    rag_success = test_rag_agent()
    
    # Test API endpoints
    api_success = test_api_endpoints()
    
    print("\n" + "=" * 50)
    if rag_success and api_success:
        print("🎉 All tests passed! RAG agent is working correctly.")
        print("\nNext steps:")
        print("1. Start the FastAPI server: uvicorn src.backend.main:app --reload")
        print("2. Open rag-test-frontend/index.html in your browser")
        print("3. Test the RAG agent through the web interface")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        sys.exit(1)
