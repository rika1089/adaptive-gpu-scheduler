"""
services/parser.py
Parses the adaptive-gpu-paper output files into structured dicts.

Path resolution: walks up from this file to find the project root
by looking for the 'output/' directory. Works on Windows and Linux.
"""
import csv
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime


def _find_project_root() -> Path:
    """
    Walk up the directory tree from this file until we find
    the adaptive-gpu-paper root (identified by output/ and configs/ dirs).
    Falls back to CWD if not found.
    """
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "output").exists() and (parent / "configs").exists():
            return parent
    # Fallback: assume we're running from project root or backend/
    cwd = Path.cwd()
    if (cwd / "output").exists():
        return cwd
    if (cwd.parent / "output").exists():
        return cwd.parent
    return cwd


PROJECT_ROOT = _find_project_root()
OUTPUT_DIR   = PROJECT_ROOT / "output"
METRICS_DIR  = OUTPUT_DIR / "metrics"
FIGURES_DIR  = OUTPUT_DIR / "figures"
REPORTS_DIR  = OUTPUT_DIR / "reports"


def parse_comparison_summary(run_id: str = "latest") -> Dict:
    """
    Parse comparison_summary.json OR aggregate from individual CSVs.
    Returns a dict of all policies found in the run's folder.
    """
    folder = METRICS_DIR if run_id == "latest" else OUTPUT_DIR / "runs" / run_id / "metrics"
    if not folder.exists():
        return {}

    # 1. Try loading the official JSON first
    json_path = folder / "comparison_summary.json"
    comparison = {}
    if json_path.exists():
        try:
            with open(json_path) as f:
                raw = json.load(f)
            for pol, data in raw.items():
                fairness = data.pop("_fairness", 1.0)
                comparison[pol] = {"agents": data, "fairness": fairness}
        except Exception: pass

    # 2. Find ALL policies that have CSVs and fill in any missing ones
    # This is crucial because runner.py runs policies one-by-one and overwrites the JSON.
    for csv_file in folder.glob("*_repeat0_metrics.csv"):
        policy_name = csv_file.name.split("_repeat0_metrics.csv")[0]
        if policy_name not in comparison:
            # We found a CSV for a policy that's not in our summary JSON!
            # Let's aggregate it manually.
            policy_data = _aggregate_policy_from_csv(csv_file)
            if policy_data:
                comparison[policy_name] = policy_data

    return comparison

def _aggregate_policy_from_csv(csv_path: Path) -> Optional[Dict]:
    """Helper to calculate average metrics from a single metrics CSV file."""
    try:
        from collections import defaultdict
        agent_agg = defaultdict(lambda: defaultdict(list))
        
        with open(csv_path, newline="") as f:
            for row in csv.DictReader(f):
                agent = row["agent"]
                agent_agg[agent]["avg_latency_ms"].append(float(row["avg_latency_ms"]))
                agent_agg[agent]["avg_throughput"].append(float(row["throughput"]))
                agent_agg[agent]["avg_gpu_share"].append(float(row["gpu_share"]))
                agent_agg[agent]["avg_sla_violation"].append(float(row["sla_violation_rate"]))

        if not agent_agg: return None

        agents_data = {}
        for agent, metrics in agent_agg.items():
            agents_data[agent] = {
                k: round(sum(v)/len(v), 4) for k, v in metrics.items()
            }
        
        # Approximate fairness (we don't have the raw allocation data here easily, 
        # so we default to 1.0 or skip it)
        return {"agents": agents_data, "fairness": 1.0}
    except Exception:
        return None


def parse_metrics_csv(policy: str, repeat: int = 0) -> List[Dict]:
    """Parse output/metrics/{policy}_repeat{n}_metrics.csv"""
    path = METRICS_DIR / f"{policy}_repeat{repeat}_metrics.csv"
    if not path.exists():
        return []
    rows = []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            rows.append({
                "elapsed_s":        float(row["elapsed_s"]),
                "policy":           row["policy"],
                "workload":         row["workload"],
                "agent":            row["agent"],
                "queue_length":     int(row["queue_length"]),
                "arrival_rate":     float(row["arrival_rate"]),
                "avg_latency_ms":   float(row["avg_latency_ms"]),
                "throughput":       float(row["throughput"]),
                "sla_violation_rate": float(row["sla_violation_rate"]),
                "gpu_share":        float(row["gpu_share"]),
                "timestamp":        float(row["timestamp"]),
            })
    return rows


def parse_allocations_csv(policy: str, repeat: int = 0) -> List[Dict]:
    """Parse output/metrics/{policy}_repeat{n}_allocations.csv"""
    path = METRICS_DIR / f"{policy}_repeat{repeat}_allocations.csv"
    if not path.exists():
        return []
    rows = []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            rows.append({
                "timestamp":  float(row["timestamp"]),
                "policy":     row["policy"],
                "coord":      float(row.get("coord", 0)),
                "nlp":        float(row.get("nlp", 0)),
                "vision":     float(row.get("vision", 0)),
                "reasoning":  float(row.get("reasoning", 0)),
            })
    if rows:
        t0 = rows[0]["timestamp"]
        for r in rows:
            r["elapsed_s"] = round(r["timestamp"] - t0, 2)
    return rows


def list_available_runs() -> List[Dict]:
    """Return list of runs by scanning output/runs/ directory"""
    runs_dir = OUTPUT_DIR / "runs"
    if not runs_dir.exists():
        # Fallback to output/metrics if runs dir doesn't exist yet
        return [_get_run_data("latest", METRICS_DIR)] if METRICS_DIR.exists() else []

    all_runs = []
    # Check "latest" first
    if METRICS_DIR.exists():
        all_runs.append(_get_run_data("latest", METRICS_DIR))

    # Scan for archived runs
    for run_folder in sorted(runs_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
        if run_folder.is_dir() and (run_folder / "metrics").exists():
            all_runs.append(_get_run_data(run_folder.name, run_folder / "metrics"))

    # Return top 10 unique runs
    seen = set()
    unique_runs = []
    for r in all_runs:
        if r["run_id"] not in seen:
            unique_runs.append(r)
            seen.add(r["run_id"])
    
    return unique_runs[:10]

def _get_run_data(run_id: str, metrics_dir: Path) -> Dict:
    """Helper to extract run metadata from a directory"""
    policies_found = set()
    for f in metrics_dir.glob("*_repeat0_metrics.csv"):
        policy = f.stem.replace("_repeat0_metrics", "")
        policies_found.add(policy)

    if not policies_found:
        return {
            "run_id": run_id,
            "run_name": f"Run: {run_id}",
            "started_at": datetime.now().isoformat(),
            "duration_seconds": 0,
            "policies": [],
            "workload": "unknown",
            "repeats": 0,
            "status": "incomplete",
            "has_results": False,
            "summary_preview": {},
        }

    mtime = max(
        (metrics_dir / f"{p}_repeat0_metrics.csv").stat().st_mtime
        for p in policies_found
        if (metrics_dir / f"{p}_repeat0_metrics.csv").exists()
    )
    ts = datetime.fromtimestamp(mtime).isoformat()

    summary = parse_comparison_summary(run_id)
    preview: Dict[str, Any] = {}
    if summary:
        for pol, data in summary.items():
            agents = data.get("agents", {})
            coords = agents.get("coord", {})
            preview[pol] = {
                "coord_latency": coords.get("avg_latency_ms", 0),
                "fairness":      data.get("fairness", 0),
            }

    meta = {}
    meta_path = metrics_dir / "metadata.json"
    if meta_path.exists():
        try:
            with open(meta_path) as f:
                meta = json.load(f)
        except Exception: pass

    return {
        "run_id":           run_id,
        "run_name":         f"Run: {meta.get('workload', run_id)}",
        "started_at":       ts,
        "duration_seconds": meta.get("duration_seconds", 300),
        "policies":         sorted(list(policies_found)),
        "workload":         meta.get("workload", "paper_default"),
        "repeats":          meta.get("repeats", 1),
        "status":           "completed",
        "has_results":      True,
        "summary_preview":  preview,
    }


def list_figure_files() -> List[str]:
    if not FIGURES_DIR.exists():
        return []
    return [f.name for f in FIGURES_DIR.glob("*.png")]


def get_configs() -> Dict:
    """Return workload and policy config options."""
    try:
        import sys
        src_dir = str(PROJECT_ROOT / "src")
        if src_dir not in sys.path:
            sys.path.insert(0, src_dir)
        from adaptive_gpu.config.loader import load_all
        agents_cfg, workloads_cfg, policies_cfg, _ = load_all()
        return {
            "workloads": {
                name: {
                    "description":    w.description,
                    "duration_seconds": w.duration_seconds,
                    "arrival_rates":  w.arrival_rates,
                }
                for name, w in workloads_cfg.workloads.items()
            },
            "policies": list(policies_cfg.policies.keys()),
            "agents":   list(agents_cfg.agents.keys()),
        }
    except Exception:
        return {
            "workloads": {
                "paper_default": {
                    "description": "Paper Table 1 workload",
                    "duration_seconds": 300,
                    "arrival_rates": {"coord": 80, "nlp": 40, "vision": 45, "reasoning": 25},
                }
            },
            "policies": ["adaptive", "static", "round_robin"],
            "agents":   ["coord", "nlp", "vision", "reasoning"],
        }
