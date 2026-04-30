from app.services.parser import parse_comparison_summary, PROJECT_ROOT, METRICS_DIR
import os

print(f"Project Root: {PROJECT_ROOT}")
print(f"Metrics Dir: {METRICS_DIR}")
print(f"Exists: {METRICS_DIR.exists()}")

summary = parse_comparison_summary()
if summary:
    print("Summary found!")
    for pol, data in summary.items():
        print(f"  Policy: {pol}, Agents: {list(data['agents'].keys())}")
else:
    print("Summary NOT found")

# Check for files in metrics
if METRICS_DIR.exists():
    print(f"Files in metrics: {os.listdir(METRICS_DIR)}")
