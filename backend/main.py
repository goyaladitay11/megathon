import os
import sys
from pathlib import Path

# Ensure both backend root and repo root are in sys.path
backend_dir = Path(__file__).resolve().parent
repo_root = backend_dir.parent
for p in [str(backend_dir), str(repo_root)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.api.v1.routes import router as api_v1_router
from routes.demo import router as demo_router

app = FastAPI(
    title="Lloyds Green Home Score & Retrofit Engine API",
    description="Lloyds Megathon X (Problem Statement 2: Singularity) - Green Home Score, Retrofit Recommendation Engine & Grounded What-If AI",
    version="1.0.0",
)

# Robust CORS configuration
origins = settings.cors_origins_list
if "*" not in origins and "http://localhost:3000" not in origins:
    origins.extend(["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173", "http://127.0.0.1:5173"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "service": "lloyds-green-home-api",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "emissions_factors_source": settings.EMISSION_FACTORS_SOURCE,
        "gemini_active": bool(settings.GEMINI_API_KEY),
    }

# Mount API routes
app.include_router(api_v1_router, prefix="/api")
app.include_router(demo_router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.API_HOST, port=settings.API_PORT, reload=True)
