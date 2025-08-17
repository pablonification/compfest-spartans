from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .routers import health, scan, auth, ws
from pathlib import Path
from .db.mongo import connect_to_mongo, close_mongo_connection
from .middleware.auth_middleware import AuthMiddleware

app = FastAPI()

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

# Add authentication middleware
app.add_middleware(AuthMiddleware)

app.include_router(health.router)
app.include_router(scan.router)
app.include_router(auth.router, prefix="/auth")
app.include_router(ws.router)

# Serve saved debug images under /debug
app.mount("/debug", StaticFiles(directory="debug_images"), name="debug")


@app.on_event("startup")
async def on_startup() -> None:
    await connect_to_mongo()


@app.on_event("shutdown")
async def on_shutdown() -> None:
    await close_mongo_connection()


@app.get("/")
def read_root():
    return {"Hello": "FastAPI Backend"}