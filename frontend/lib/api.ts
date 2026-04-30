const BASE = typeof window !== 'undefined'
  ? (process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000')
  : 'http://localhost:8000'

async function fetchJSON(url: string, opts?: RequestInit) {
  // Add cache buster to URL
  const sep = url.includes('?') ? '&' : '?'
  const busterUrl = `${url}${sep}_t=${Date.now()}`
  
  const res = await fetch(busterUrl, {
    ...opts,
    cache: 'no-store', // Disable browser cache
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body?.detail ?? `HTTP ${res.status}`)
  }
  return res.json()
}

export const api = {
  /** Check if backend is alive */
  health: () =>
    fetch(`${BASE}/health`, { signal: AbortSignal.timeout(2000) })
      .then(r => r.ok)
      .catch(() => false),

  /** POST /experiments/run — start an experiment run */
  runExperiment: (body: {
    policies: string[]
    workload: string
    duration_seconds: number
    repeats: number
    random_seed: number
    run_name?: string
  }) =>
    fetchJSON(`${BASE}/experiments/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }),

  /** POST /experiments/stop */
  stopExperiment: () =>
    fetchJSON(`${BASE}/experiments/stop`, { method: 'POST' }),

  /** GET /experiments/status */
  getStatus: () =>
    fetchJSON(`${BASE}/experiments/status`),

  /** GET /experiments/configs */
  getConfigs: () =>
    fetchJSON(`${BASE}/experiments/configs`),

  /** GET /results/summary */
  getSummary: () =>
    fetchJSON(`${BASE}/results/summary`),

  /** GET /results/run/{runId}/all-metrics */
  getAllMetrics: (runId = 'latest') =>
    fetchJSON(`${BASE}/results/run/${runId}/all-metrics`),

  /** GET /results/run/{runId}/all-allocations */
  getAllAllocations: (runId = 'latest') =>
    fetchJSON(`${BASE}/results/run/${runId}/all-allocations`),

  /** GET /results/runs */
  getRuns: () =>
    fetchJSON(`${BASE}/results/runs`),

  /** GET /results/files */
  getFiles: () =>
    fetchJSON(`${BASE}/results/files`),

  /** Build a download URL */
  downloadUrl: (type: string, filename: string) =>
    `${BASE}/results/download/${type}/${filename}`,
}
