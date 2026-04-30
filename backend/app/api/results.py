from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from app.services.parser import (
    parse_comparison_summary, parse_metrics_csv,
    parse_allocations_csv, list_available_runs,
    list_figure_files, FIGURES_DIR, METRICS_DIR, REPORTS_DIR
)

router = APIRouter(prefix="/results", tags=["results"])


@router.get("/summary")
async def get_summary():
    data = parse_comparison_summary()
    if data is None:
        raise HTTPException(status_code=404, detail="No summary found. Run an experiment first.")
    return data


@router.get("/runs")
async def list_runs():
    return list_available_runs()


@router.get("/run/{run_id}/metrics")
async def get_run_metrics(run_id: str, policy: str = "adaptive", repeat: int = 0):
    rows = parse_metrics_csv(policy, repeat)
    return {"policy": policy, "repeat": repeat, "rows": rows}


@router.get("/run/{run_id}/allocations")
async def get_run_allocations(run_id: str, policy: str = "adaptive", repeat: int = 0):
    rows = parse_allocations_csv(policy, repeat)
    return {"policy": policy, "repeat": repeat, "rows": rows}


@router.get("/run/{run_id}/all-metrics")
async def get_all_metrics(run_id: str):
    """Return metrics for all policies in one call."""
    result = {}
    for policy in ["adaptive", "static", "round_robin"]:
        rows = parse_metrics_csv(policy, 0)
        if rows:
            result[policy] = rows
    return result


@router.get("/run/{run_id}/all-allocations")
async def get_all_allocations(run_id: str):
    result = {}
    for policy in ["adaptive", "static", "round_robin"]:
        rows = parse_allocations_csv(policy, 0)
        if rows:
            result[policy] = rows
    return result


@router.get("/files")
async def list_files():
    figs = list_figure_files()
    csvs = [f.name for f in METRICS_DIR.glob("*.csv")] if METRICS_DIR.exists() else []
    jsons = [f.name for f in REPORTS_DIR.glob("*.json")] if REPORTS_DIR.exists() else []
    return {"figures": figs, "csvs": csvs, "reports": jsons}


@router.get("/download/figure/{filename}")
async def download_figure(filename: str):
    path = FIGURES_DIR / filename
    if not path.exists():
        path = METRICS_DIR / filename  # Fallback
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path, media_type="image/png", filename=filename)


@router.get("/download/csv/{filename}")
async def download_csv(filename: str):
    path = METRICS_DIR / filename
    if not path.exists():
        path = REPORTS_DIR / filename  # Fallback
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path, media_type="text/csv", filename=filename)


@router.get("/download/report/{filename}")
async def download_report(filename: str):
    path = REPORTS_DIR / filename
    if not path.exists():
        path = METRICS_DIR / filename  # Fallback
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path, media_type="application/json", filename=filename)
