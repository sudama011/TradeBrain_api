from fastapi import FastAPI
from app.api import signals
from app.database import engine, Base
import app.models

# 1. Create Tables automatically on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(title="TradeBrain API", version="0.1.0")

app.include_router(signals.router, prefix="/api/v1")

@app.get("/")
def root():
    return {"message": "TradeBrain Neural Net Online 🧠"}