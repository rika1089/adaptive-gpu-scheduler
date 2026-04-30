# Adaptive GPU Scheduler — Frontend Dashboard

## Quick Start

```bash
# 1. Start backend
cd ../backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 2. Start frontend (standalone HTML — no build needed)
open dashboard.html      # works instantly, loads real data from backend

# 3. OR start Next.js dev server
npm install
npm run dev              # http://localhost:3000
```

## File Map to Backend Outputs

| Frontend Component          | Backend Source                          |
|-----------------------------|----------------------------------------|
| KPI cards (latency etc.)    | output/reports/comparison_summary.json |
| Policy comparison table     | output/reports/comparison_summary.json |
| Latency/throughput charts   | output/metrics/*_metrics.csv           |
| GPU allocation bars         | output/metrics/*_allocations.csv       |
| Fairness gauges             | comparison_summary.json._fairness      |
| Terminal logs               | ws://localhost:8000/ws/logs            |
| Download buttons            | GET /results/download/{type}/{file}    |

## API Contract

| Method | Endpoint                         | Purpose                        |
|--------|----------------------------------|-------------------------------|
| POST   | /experiments/run                 | Start experiment run           |
| POST   | /experiments/stop                | Stop running experiment        |
| GET    | /experiments/status              | Poll run progress              |
| GET    | /experiments/configs             | Get workload/policy options    |
| GET    | /results/summary                 | comparison_summary.json        |
| GET    | /results/run/{id}/all-metrics    | All policy metrics CSVs        |
| GET    | /results/run/{id}/all-allocations| All allocation CSVs            |
| GET    | /results/files                   | List downloadable files        |
| WS     | /ws/logs                         | Stream experiment log lines    |
