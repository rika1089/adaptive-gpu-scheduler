"""
app/main.py — FastAPI application entry point.

Import resolution note:
  All internal imports use  `from app.XXX import ...`
  This works when Python's sys.path contains the `backend/` directory.
  Use `python start.py` (from backend/) or `python -m uvicorn app.main:app`
  instead of bare `uvicorn app.main:app` to ensure the path is set correctly.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.experiments import router as exp_router
from app.api.results     import router as results_router
from app.api.websocket   import router as ws_router

from pathlib import Path
import sys

# Ensure project root / src is on path for adaptive_gpu imports
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

app = FastAPI(
    title       = "Adaptive GPU Scheduler API",
    description = "Backend for the Adaptive GPU Resource Allocation dashboard",
    version     = "1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["http://localhost:3000", "http://127.0.0.1:3000",
                         "http://localhost:3001", "http://127.0.0.1:3001"],
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)


@app.get("/")
async def root():
    return {
        "message": "Adaptive GPU Scheduler API is running",
        "docs": "/docs",
        "health": "/health",
        "version": "1.0.0"
    }


app.include_router(exp_router)
app.include_router(results_router)
app.include_router(ws_router)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "service": "adaptive-gpu-scheduler", "version": "1.0.0"}
