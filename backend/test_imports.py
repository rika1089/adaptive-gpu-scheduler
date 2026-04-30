import sys
from pathlib import Path

# Try to import app
try:
    import app
    print("Import 'app' success")
except ImportError as e:
    print(f"Import 'app' failed: {e}")

# Try to import adaptive_gpu
try:
    import adaptive_gpu
    print("Import 'adaptive_gpu' success")
except ImportError as e:
    print(f"Import 'adaptive_gpu' failed: {e}")

# Check project root detection
here = Path(__file__).resolve()
for p in here.parents:
    if (p / "output").exists() and (p / "configs").exists():
        print(f"Project root detected: {p}")
        break
else:
    print("Project root NOT detected")
