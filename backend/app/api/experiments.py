from fastapi import APIRouter, HTTPException
from app.schemas.experiment import ExperimentRequest, ExperimentStatus, RunStatus
from app.services import runner
from app.services.parser import get_configs

router = APIRouter(prefix="/experiments", tags=["experiments"])


@router.post("/run")
async def run_experiment(request: ExperimentRequest):
    if runner.get_status()["status"] == "running":
        raise HTTPException(status_code=409, detail="An experiment is already running")
    # Use mode='json' to ensure Enums are converted to strings for the runner's state
    run_id = runner.run_experiment(request.model_dump(mode='json'))
    return {"run_id": run_id, "message": "Experiment started"}


@router.post("/stop")
async def stop_experiment():
    runner.stop_experiment()
    return {"message": "Stop signal sent"}


@router.get("/status", response_model=ExperimentStatus)
async def get_status():
    s = runner.get_status()

    raw_status = s.get("status", "idle")
    try:
        status = RunStatus(raw_status)
    except ValueError:
        status = RunStatus.idle  # or whatever default you prefer

    return ExperimentStatus(
        run_id=s.get("run_id") or "none",
        status=status,
        current_policy=s.get("current_policy"),
        current_repeat=s.get("current_repeat", 0),
        total_repeats=s.get("total_repeats", 0),
        elapsed_seconds=s.get("elapsed_seconds", 0.0),
        estimated_remaining=s.get("estimated_remaining", 0.0),
        progress_pct=s.get("progress_pct", 0.0),
        started_at=s.get("started_at"),
        message=s.get("message", ""),
    )


@router.get("/configs")
async def get_experiment_configs():
    return get_configs()
