# 🐳 SmartBin RAG Agent - Docker Testing Setup

Complete testing environment for the SmartBin RAG agent with Docker.

## 🚀 Quick Start

```bash
# 1. Set your Google AI API key
export GOOGLE_API_KEY=your_actual_api_key_here

# 2. Start all services
docker-compose up -d --build

# 3. Check status
docker-compose ps
```

## 📋 Prerequisites

1. **Docker Desktop** running
2. **Google AI API Key** (for Gemini 2.0 Flash)
   - Get one at: https://makersuite.google.com/app/apikey

## ⚙️ Configuration

### Environment Variables
Set these before running `docker-compose up`:

```bash
# Required for RAG agent
export GOOGLE_API_KEY=your_google_api_key_here

# Optional - for full SmartBin functionality
export MONGODB_URI=mongodb://localhost:27017
export MONGODB_DB_NAME=smartbin
export GOOGLE_CLIENT_ID=your_google_client_id
export GOOGLE_CLIENT_SECRET=your_google_client_secret
export JWT_SECRET_KEY=your_jwt_secret
```

## 🌐 Services & Ports

| Service | Port | URL | Purpose |
|---------|------|-----|---------|
| **Backend API** | 8000 | http://localhost:8000 | FastAPI + RAG Agent |
| **Main Frontend** | 3000 | http://localhost:3000 | SmartBin Next.js app |
| **RAG Test UI** | 8080 | http://localhost:8080 | RAG testing interface |
| **MongoDB** | 27017 | localhost:27017 | Database |
| **Redis** | 6379 | localhost:6379 | Cache |
| **IoT Simulator** | 8080 | http://localhost:8080 | IoT simulation |

## 🧠 RAG Agent Endpoints

- **Health Check**: `GET http://localhost:8000/rag/health`
- **Query**: `POST http://localhost:8000/rag/query`
- **Thread History**: `GET http://localhost:8000/rag/threads/{id}/history`

## 💡 Testing the RAG Agent

1. **Start services**: `docker-compose up -d --build`
2. **Open test interface**: http://localhost:8080
3. **Set API URL**: http://localhost:8000
4. **Try sample questions**:
   - "Jelaskan hierarki pengelolaan sampah 3R dan 5R"
   - "Apa itu SmartBin dan bagaimana cara kerjanya?"
   - "Bagaimana proses daur ulang plastik PET?"

## 🛠️ Useful Commands

```bash
# Start all services
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Restart services
docker-compose restart

# Check status
docker-compose ps

# Rebuild specific service
docker-compose up -d --build backend
```

## 🔍 Troubleshooting

### "GOOGLE_API_KEY not set"
- Make sure you've exported the environment variable before running docker-compose
- Check: `echo $GOOGLE_API_KEY`

### "Port already in use"
- Stop existing services: `docker-compose down`
- Check what's using the port: `lsof -i :8000`

### "Build failed"
- Check Docker has enough memory (at least 4GB)
- Try: `docker system prune` to free space

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   RAG Test UI  │    │   Main Frontend │    │   IoT Simulator │
│   (Port 8080)  │    │   (Port 3000)   │    │   (Port 8080)   │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │      Backend API          │
                    │      (Port 8000)         │
                    │  ┌─────────────────────┐  │
                    │  │   RAG Agent        │  │
                    │  │  (Gemini 2.0)      │  │
                    │  └─────────────────────┘  │
                    └─────────────┬─────────────┘
                                  │
                    ┌─────────────▼─────────────┐
                    │      MongoDB             │
                    │      (Port 27017)        │
                    └───────────────────────────┘
```

## 🔄 Development Workflow

1. **Start environment**: `docker-compose up -d --build`
2. **Make code changes** in your editor
3. **Rebuild**: `docker-compose up -d --build backend`
4. **Test changes** at http://localhost:8080
5. **View logs**: `docker-compose logs -f backend`

## 🎯 What's Included

- ✅ **RAG Agent**: Google Gemini 2.0 Flash + LangGraph
- ✅ **Knowledge Base**: SmartBin markdown documentation
- ✅ **Vector Store**: ChromaDB for semantic search
- ✅ **API**: FastAPI with RAG endpoints
- ✅ **Frontend**: HTML testing interface
- ✅ **Database**: MongoDB + Redis
- ✅ **IoT Simulator**: For testing sensor data

## 🚀 Production Notes

This setup is for **testing and development only**. For production:

- Use proper secrets management
- Set up SSL/TLS certificates
- Configure proper CORS policies
- Use production-grade databases
- Set up monitoring and logging
- Implement proper authentication

---

**Happy testing! 🧠✨**
