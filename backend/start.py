"""
start.py — Cross-platform uvicorn launcher.

Run from the backend/ directory:
    python start.py

Or from the project root:
    python backend/start.py
"""
import sys
import os
from pathlib import Path

# Ensure backend/ is on sys.path so `import app` works
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Also put project root on sys.path so adaptive_gpu can be imported
PROJECT_ROOT = BACKEND_DIR.parent
SRC_DIR = PROJECT_ROOT / "src"
if SRC_DIR.exists() and str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

os.chdir(BACKEND_DIR)  # ensure relative paths resolve from backend/

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        reload_dirs=[str(BACKEND_DIR)],
    )
