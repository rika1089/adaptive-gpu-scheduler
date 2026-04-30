#!/bin/bash
# scripts/launch_all.sh
# Launch all 4 vLLM agents as background processes on DGX H200.
# Uses CUDA_VISIBLE_DEVICES for GPU assignment (no Docker needed).
#
# Usage:
#   bash scripts/launch_all.sh
#   bash scripts/launch_all.sh --util 0.5   # set GPU memory utilization

set -e

GPU_UTIL=${2:-0.40}
MODELS=/nfsshare/users/sreekar/models
LOG_DIR=output/logs/dgx

mkdir -p "$LOG_DIR"

echo "Stopping any existing vLLM processes..."
pkill -f "vllm.entrypoints" 2>/dev/null || true
sleep 2

echo ""
echo "Starting agents (GPU utilization: $GPU_UTIL)"
echo "─────────────────────────────────────────────"

echo "  coord     → port 8001 on GPU 5"
CUDA_VISIBLE_DEVICES=5 python -m vllm.entrypoints.openai.api_server \
    --model "$MODELS/phi3" --port 8001 \
    --max-model-len 2048 --gpu-memory-utilization "$GPU_UTIL" \
    > "$LOG_DIR/coord.log" 2>&1 &

sleep 5

echo "  nlp       → port 8002 on GPU 6"
CUDA_VISIBLE_DEVICES=6 python -m vllm.entrypoints.openai.api_server \
    --model "$MODELS/qwen" --port 8002 \
    --max-model-len 2048 --gpu-memory-utilization "$GPU_UTIL" \
    > "$LOG_DIR/nlp.log" 2>&1 &

sleep 5

echo "  vision    → port 8003 on GPU 7"
CUDA_VISIBLE_DEVICES=7 python -m vllm.entrypoints.openai.api_server \
    --model "$MODELS/tinyllama" --port 8003 \
    --max-model-len 2048 --gpu-memory-utilization "$GPU_UTIL" \
    > "$LOG_DIR/vision.log" 2>&1 &

sleep 5

echo "  reasoning → port 8004 on GPU 5 (shares with coord)"
CUDA_VISIBLE_DEVICES=5 python -m vllm.entrypoints.openai.api_server \
    --model "$MODELS/phi3" --port 8004 \
    --max-model-len 2048 --gpu-memory-utilization "$GPU_UTIL" \
    > "$LOG_DIR/reasoning.log" 2>&1 &

echo ""
echo "All agents launched. Checking readiness..."
echo "(This may take 60–120 seconds.)"
echo ""

check_port() {
    local name=$1
    local port=$2
    for i in $(seq 1 120); do
        if curl -sf "http://localhost:$port/v1/models" > /dev/null 2>&1; then
            echo "  ✓ $name ready (${i}s)"
            return 0
        fi
        sleep 1
    done
    echo "  ✗ $name TIMEOUT — check $LOG_DIR/$name.log"
    return 1
}

check_port "coord"     8001
check_port "nlp"       8002
check_port "vision"    8003
check_port "reasoning" 8004

echo ""
echo "All checks complete."
echo "Logs: $LOG_DIR/"
echo "Now run: python experiments/exp_realworld_stub.py"
