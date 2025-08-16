from fastapi import FastAPI

from .routers import health

app = FastAPI()

app.include_router(health.router)


@app.get("/")
def read_root():
    return {"Hello": "FastAPI Backend"}