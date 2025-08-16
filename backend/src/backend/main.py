from fastapi import FastAPI

from .routers import health, scan
from .db.mongo import connect_to_mongo, close_mongo_connection

app = FastAPI()

app.include_router(health.router)
app.include_router(scan.router)


@app.on_event("startup")
async def on_startup() -> None:
    await connect_to_mongo()


@app.on_event("shutdown")
async def on_shutdown() -> None:
    await close_mongo_connection()


@app.get("/")
def read_root():
    return {"Hello": "FastAPI Backend"}