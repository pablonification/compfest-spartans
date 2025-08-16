from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "FastAPI Backend"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}