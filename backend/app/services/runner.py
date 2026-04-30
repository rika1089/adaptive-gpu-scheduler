"""
services/runner.py
Runs adaptive-gpu-paper experiments as a background thread.
Broadcasts log lines to asyncio queues for WebSocket consumers.
Status is always readable via get_status().
"""
import asyncio
import os
import subprocess
import sys
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, List

def _find_root() -> Path:
    here = Path(__file__).resolve()
    for p in here.parents:
        if (p / "output").exists() and (p / "configs").exists():
            return p
    return Path.cwd()

PROJECT_ROOT = _find_root()

# ── Global mutable state (protected by _lock) ────────────────────────────────
_lock = threading.Lock()
_current_run: dict = {
    "run_id":            None,
    "status":            "idle",
    "current_policy":    None,
    "current_repeat":    0,
    "total_repeats":     0,
    "elapsed_seconds":   0.0,
    "estimated_remaining": 0.0,
    "progress_pct":      0.0,
    "started_at":        None,
    "message":           "",
    "request":           None,
}

_log_subscribers: List[asyncio.Queue] = []
_stop_flag  = threading.Event()
_run_thread: Optional[threading.Thread] = None


# ── Public API ────────────────────────────────────────────────────────────────

def get_status() -> dict:
    with _lock:
        return dict(_current_run)


def subscribe_logs() -> asyncio.Queue:
    q: asyncio.Queue = asyncio.Queue(maxsize=1000)
    _log_subscribers.append(q)
    return q


def unsubscribe_logs(q: asyncio.Queue) -> None:
    try:
        _log_subscribers.remove(q)
    except ValueError:
        pass


def run_experiment(request: dict) -> str:
    global _run_thread
    with _lock:
        if _current_run["status"] == "running":
            return _current_run["run_id"] or ""

    run_id = str(uuid.uuid4())[:8]
    _stop_flag.clear()
    _update(
        run_id=run_id,
        status="running",
        current_policy=None,
        current_repeat=0,
        total_repeats=request.get("repeats", 1) * len(request.get("policies", [])),
        elapsed_seconds=0.0,
        estimated_remaining=0.0,
        progress_pct=0.0,
        started_at=datetime.now().isoformat(),
        message="Starting…",
        request=request,
    )

    _run_thread = threading.Thread(
        target=_run_worker, args=(run_id, request), daemon=True, name=f"run-{run_id}"
    )
    _run_thread.start()
    return run_id


def stop_experiment() -> None:
    _stop_flag.set()
    _update(status="stopped", message="Stopped by user")
    _broadcast("⛔  Experiment stopped by user.")


# ── Internal helpers ──────────────────────────────────────────────────────────

def _update(**kwargs) -> None:
    with _lock:
        _current_run.update(kwargs)


def _broadcast(line: str) -> None:
    for q in list(_log_subscribers):
        try:
            q.put_nowait(line)
        except Exception:
            pass


def _run_worker(run_id: str, request: dict) -> None:
    policies  = request.get("policies", ["adaptive", "static", "round_robin"])
    workload  = request.get("workload", "paper_default")
    duration  = int(request.get("duration_seconds", 60))
    repeats   = int(request.get("repeats", 1))
    seed      = int(request.get("random_seed", 42))

    total_steps = len(policies) * repeats
    step        = 0
    t_start     = time.time()

    env = {**os.environ, "PYTHONPATH": str(PROJECT_ROOT / "src")}

    # 1. Prepare directories
    live_dir = PROJECT_ROOT / "output" / "metrics"
    run_output_dir = PROJECT_ROOT / "output" / "runs" / run_id / "metrics"
    
    # Clear old live metrics to ensure fresh start
    if live_dir.exists():
        for f in live_dir.glob("*.csv"): f.unlink()
        for f in live_dir.glob("*.json"): f.unlink()
    live_dir.mkdir(parents=True, exist_ok=True)
    run_output_dir.mkdir(parents=True, exist_ok=True)

    try:
        _broadcast(f"🚀  Run {run_id} started")
        _broadcast(f"    Policies : {', '.join(policies)}")
        _broadcast(f"    Workload : {workload}")
        _broadcast(f"    Duration : {duration}s × {repeats} repeat(s)")
        _broadcast("─" * 56)

        for policy in policies:
            for repeat in range(repeats):
                if _stop_flag.is_set():
                    break

                step += 1
                elapsed = round(time.time() - t_start, 1)
                pct     = round((step - 1) / total_steps * 100, 1)
                remaining = max(0, (total_steps - step + 1) * duration - elapsed % duration)

                _update(
                    current_policy=policy,
                    current_repeat=repeat,
                    total_repeats=total_steps,
                    elapsed_seconds=elapsed,
                    estimated_remaining=round(remaining, 1),
                    progress_pct=pct,
                    message=f"Running {policy} repeat {repeat + 1}/{repeats}",
                )
                _broadcast(f"\n▶  Policy: {policy.upper()}   Repeat: {repeat + 1}/{repeats}")

                # Use a unique output directory for this run
                run_output_dir = PROJECT_ROOT / "output" / "runs" / run_id / "metrics"
                run_output_dir.mkdir(parents=True, exist_ok=True)

                # Build the CLI command
                cmd = [
                    sys.executable, "-m", "adaptive_gpu.main",
                    "--policy",     policy,
                    "--workload",   workload,
                    "--duration",   str(duration),
                    "--repeats",    "1",
                    "--output-dir", str(live_dir),
                    "--figures-dir","output/figures",
                    "--no-plots",                       # skip matplotlib during run
                ]

                try:
                    proc = subprocess.Popen(
                        cmd,
                        cwd=str(PROJECT_ROOT),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        env=env,
                        bufsize=1,
                    )

                    for raw_line in proc.stdout:         # type: ignore[union-attr]
                        if _stop_flag.is_set():
                            proc.terminate()
                            break
                        stripped = raw_line.rstrip()
                        if stripped:
                            _broadcast(stripped)
                            now = time.time()
                            _update(
                                elapsed_seconds=round(now - t_start, 1),
                                estimated_remaining=max(0, round(
                                    (total_steps - step) * duration - (now - t_start) % duration, 1
                                )),
                            )

                    proc.wait()
                    rc = proc.returncode
                    if rc != 0 and not _stop_flag.is_set():
                        _broadcast(f"[Warn] {policy} exited with code {rc}")

                except FileNotFoundError:
                    _broadcast(f"[Warn] Could not find Python / adaptive_gpu module.")
                    _broadcast(f"[Warn] Ensure you ran: pip install -e . from {PROJECT_ROOT}")
                except Exception as exc:
                    _broadcast(f"❌  Subprocess error: {exc}")

                _broadcast(f"✅  {policy} repeat {repeat + 1} complete")

            if _stop_flag.is_set():
                break

        # ── Finished ──────────────────────────────────────────────────────────
        if not _stop_flag.is_set():
            total_elapsed = round(time.time() - t_start, 1)
            _broadcast("")
            _broadcast(f"✅  All runs complete  ({total_elapsed}s total)")
            _broadcast("    Results → output/metrics/  &  output/reports/")
            _update(
                status="completed",
                progress_pct=100.0,
                elapsed_seconds=total_elapsed,
                estimated_remaining=0.0,
                message="Experiment completed successfully",
            )
            # Save metadata and archive
            try:
                import json
                meta_path = live_dir / "metadata.json"
                meta_data = {
                    "run_id": run_id,
                    "workload": workload,
                    "duration_seconds": duration,
                    "repeats": repeats,
                    "policies": policies,
                    "completed_at": datetime.now().isoformat(),
                }
                with open(meta_path, "w") as f:
                    json.dump(meta_data, f, indent=2)
                
                # Copy live results to archive
                import shutil
                if live_dir.exists():
                    for item in live_dir.iterdir():
                        if item.is_file():
                            shutil.copy2(item, run_output_dir / item.name)
                _broadcast(f"📂  Run archived to: {run_output_dir}")
            except Exception as e:
                _broadcast(f"[Warn] Failed to archive run: {e}")
        else:
            _update(status="stopped", message="Stopped by user")

    except Exception as exc:
        _broadcast(f"❌  Unexpected error: {exc}")
        _update(status="failed", message=str(exc))
