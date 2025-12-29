from fastapi import FastAPI
from app.api import signals  # We will create this next

app = FastAPI(title="TradeBrain API", version="0.1.0")

# Include the router
app.include_router(signals.router, prefix="/api/v1")

@app.get("/")
def root():
    return {"message": "TradeBrain Neural Net Online 🧠"}