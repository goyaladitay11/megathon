import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.demo import router as demo_router

load_dotenv()
app = FastAPI(title="Megathon Starter API", version="0.1.0")
origins = [origin.strip() for origin in os.getenv("FRONTEND_ORIGIN", "http://localhost:3000").split(",") if origin.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["GET", "POST"], allow_headers=["Content-Type", "Authorization"])

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "megathon-api"}

app.include_router(demo_router, prefix="/api")
