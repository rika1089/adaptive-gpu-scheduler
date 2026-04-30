#!/bin/bash
set -e
cd "$(dirname "$0")"
echo "Starting Adaptive GPU Scheduler API..."
echo "  API:  http://localhost:8000"
echo "  Docs: http://localhost:8000/docs"
echo ""
pip install -r requirements.txt -q
python start.py
