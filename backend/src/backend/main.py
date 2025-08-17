from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from .routers import health, scan, ws, auth, notification, statistics, educational
from pathlib import Path
from .db.mongo import connect_to_mongo, close_mongo_connection


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_to_mongo()
    yield
    # Shutdown
    await close_mongo_connection()


app = FastAPI(lifespan=lifespan)

# Ensure debug image directory exists
Path("debug_images").mkdir(exist_ok=True)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(scan.router)
app.include_router(ws.router)
app.include_router(auth.router)
app.include_router(notification.router)
app.include_router(statistics.router)
app.include_router(educational.router)

# Serve saved debug images under /debug
app.mount("/debug", StaticFiles(directory="debug_images"), name="debug")


@app.get("/")
def read_root():
    return {"Hello": "FastAPI Backend"}