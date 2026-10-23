from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
import os

from .database import engine, Base
from .seed_data import init_db
from .routers import telemetry, controls, ai_assistant, marketplace, alerts, cctv, weather

app = FastAPI(
    title="AgroSmart & Ulavan Connect AI - Backend API",
    description="Full-stack reverse-engineered & production-grade backend for Smart Agriculture, IoT Sensors, Automated Irrigation, Multilingual AI Voice Assistant, and Direct Farm Marketplace.",
    version="1.1.0"
)

# Private Network & CORS middleware for seamless local browser access
@app.middleware("http")
async def add_cors_and_private_network_headers(request: Request, call_next):
    if request.method == "OPTIONS":
        response = JSONResponse(content={"status": "ok"})
    else:
        response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Allow-Private-Network"] = "true"
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event to ensure database is created & seeded
@app.on_event("startup")
def startup_event():
    init_db()

# Include all API Routers
app.include_router(telemetry.router)
app.include_router(controls.router)
app.include_router(ai_assistant.router)
app.include_router(marketplace.router)
app.include_router(alerts.router)
app.include_router(cctv.router)
app.include_router(weather.router)

@app.get("/api/health")
def healthcheck():
    return {
        "status": "healthy",
        "message": "AgroSmart / Ulavan Connect AI API is running.",
        "documentation": "/docs",
        "portal": "/portal",
        "supported_languages": ["ta (Tamil & Thanglish)", "en (English)"],
        "version": "1.1.0"
    }

# Unified Portal — single entry point for everything
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "frontend")

@app.get("/portal", response_class=HTMLResponse)
def portal():
    portal_path = os.path.join(frontend_dir, "portal.html")
    with open(portal_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

# Mount Frontend directory so browsing http://localhost:8000 loads the full application seamlessly
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
