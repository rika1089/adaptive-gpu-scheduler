import subprocess
import sys
import os
import time
from pathlib import Path

def main():
    # Get project root
    root_dir = Path(__file__).resolve().parent
    
    print("\n" + "="*50)
    print("  Adaptive GPU Scheduler — Unified Launcher")
    print("="*50 + "\n")

    # 1. Start Backend (FastAPI)
    print("📦 Starting Backend (FastAPI)...")
    # Using sys.executable ensures we use the same environment
    backend_cmd = [sys.executable, "backend/start.py"]
    backend_process = subprocess.Popen(
        backend_cmd,
        cwd=root_dir,
        shell=False
    )

    # Give backend a moment to initialize
    time.sleep(2)

    # 2. Start Frontend (Next.js)
    print("💻 Starting Frontend (Next.js)...")
    frontend_dir = root_dir / "frontend"
    # shell=True is required on Windows to find npm
    frontend_process = subprocess.Popen(
        "npm run dev",
        cwd=frontend_dir,
        shell=True
    )

    print("\n" + "-"*50)
    print("✅ Both services are starting!")
    print(f"   - Backend : http://localhost:8000")
    print(f"   - Frontend: http://localhost:3000")
    print("-"*50)
    print("Press Ctrl+C to stop both services.\n")

    try:
        # Keep the script alive while processes are running
        while True:
            if backend_process.poll() is not None:
                print("\n⚠️  Backend process exited.")
                break
            if frontend_process.poll() is not None:
                print("\n⚠️  Frontend process exited.")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping services...")
    finally:
        # Graceful shutdown
        backend_process.terminate()
        frontend_process.terminate()
        print("✨ Goodbye!\n")

if __name__ == "__main__":
    main()
