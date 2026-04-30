'use client'
import { useState, useEffect, useRef, useCallback } from 'react'
import { Play, Square, RefreshCw, CheckCircle2 } from 'lucide-react'
import { useExperimentStore } from '@/store/useExperimentStore'
import { api } from '@/lib/api'
import { createLogSocket } from '@/lib/websocket'
import { WORKLOADS, POLICY_COLORS, POLICIES } from '@/lib/constants'
import { ProgressBar } from '@/components/shared/ProgressBar'
import { Badge } from '@/components/shared/Badge'
import { Spinner } from '@/components/shared/Spinner'

/* ── Shared style tokens ────────────────────────────────────────────────── */
const S = {
  label: {
    fontSize: 10, fontFamily: 'JetBrains Mono,monospace',
    color: 'rgba(255,255,255,0.3)', textTransform: 'uppercase' as const,
    letterSpacing: '0.08em', display: 'block', marginBottom: 6,
  },
  input: {
    width: '100%', background: 'var(--bg-3)',
    border: '1px solid var(--border)', borderRadius: 8,
    padding: '7px 12px', fontSize: 12,
    fontFamily: 'JetBrains Mono,monospace', color: 'rgba(255,255,255,0.7)',
    outline: 'none',
  },
  row: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: 11 } as const,
  rowLabel: { color: 'rgba(255,255,255,0.3)' },
  rowVal:   { fontFamily: 'JetBrains Mono,monospace', color: 'rgba(255,255,255,0.6)' },
}

/* ── Demo simulation when backend is offline ────────────────────────────── */
function runDemoSimulation(
  policies: string[],
  duration: number,
  repeats: number,
  addLog: (l: string) => void,
  setStatus: (s: any) => void,
  stopRef: React.MutableRefObject<boolean>,
): Promise<void> {
  return new Promise((resolve) => {
    const totalSteps = policies.length * repeats
    let step = 0
    const tStart = Date.now()

    addLog('🚀  Demo mode (backend not reachable)')
    addLog(`    Simulating ${policies.join(', ')}`)
    addLog('─'.repeat(52))

    const tick = setInterval(() => {
      if (stopRef.current) {
        clearInterval(tick)
        setStatus({ status: 'stopped', progress_pct: 0, current_policy: null })
        addLog('⛔  Stopped.')
        resolve()
        return
      }

      const elapsed = (Date.now() - tStart) / 1000
      const policyIdx  = Math.floor(step / repeats)
      const repeatIdx  = step % repeats
      const policy     = policies[policyIdx] ?? policies[policies.length - 1]
      const pct        = Math.min(100, (elapsed / (policies.length * repeats * Math.min(duration, 10))) * 100)

      setStatus({
        status: 'running',
        current_policy: policy,
        current_repeat: repeatIdx,
        total_repeats: totalSteps,
        elapsed_seconds: Math.round(elapsed),
        progress_pct: parseFloat(pct.toFixed(1)),
        message: `Demo: ${policy} repeat ${repeatIdx + 1}/${repeats}`,
      })

      // Log output every ~2s
      if (Math.round(elapsed) % 2 === 0 && Math.round(elapsed) > 0) {
        const fakeLatency = Math.round(800 + Math.random() * 600)
        addLog(`    ${policy} | latency ${fakeLatency}ms | queue ${Math.floor(Math.random()*40)}`)
      }

      if (pct >= 100) {
        clearInterval(tick)
        addLog('')
        addLog(`✅  Demo complete — ${policies.join(', ')} simulated`)
        addLog('    Start backend to run real experiments:')
        addLog('    cd backend && uvicorn app.main:app --reload')
        setStatus({ status: 'completed', progress_pct: 100, message: 'Demo complete' })
        resolve()
      }

      step = Math.floor((Date.now() - tStart) / 1000 * repeats / Math.min(duration, 10))
    }, 500)
  })
}

/* ── Component ──────────────────────────────────────────────────────────── */
export function ExperimentForm() {
  const { config, setConfig, status, setStatus, addLog, clearLogs } = useExperimentStore()
  const [loading, setLoading]     = useState(false)
  const [backendOk, setBackendOk] = useState<boolean | null>(null)   // null = unknown
  const [error, setError]         = useState<string | null>(null)

  const wsRef       = useRef<WebSocket | null>(null)
  const pollRef     = useRef<ReturnType<typeof setInterval> | null>(null)
  const demoStopRef = useRef(false)

  /* ── Backend health check ─────────────────────────────────────────────── */
  const checkBackend = useCallback(async () => {
    try {
      await fetch('http://localhost:8000/health', { signal: AbortSignal.timeout(2000) })
      setBackendOk(true)
    } catch {
      setBackendOk(false)
    }
  }, [])

  /* ── WebSocket connection ─────────────────────────────────────────────── */
  useEffect(() => {
    checkBackend()

    const WS_URL = 'ws://localhost:8000/ws/logs'
    let active = true

    const connect = () => {
      if (!active) return
      try {
        const ws = createLogSocket(
          WS_URL,
          (line) => {
            // Filter out raw JSON pings
            try { const d = JSON.parse(line); if (d.type === 'ping') return } catch {}
            addLog(line)
          },
          (data: any) => {
            const s = data as any
            const partial: any = {}
            if (s.status            != null) partial.status            = s.status
            if (s.current_policy    != null) partial.current_policy    = s.current_policy
            if (s.current_repeat    != null) partial.current_repeat    = s.current_repeat
            if (s.total_repeats     != null) partial.total_repeats     = s.total_repeats
            if (s.progress_pct      != null) partial.progress_pct      = s.progress_pct
            if (s.elapsed_seconds   != null) partial.elapsed_seconds   = s.elapsed_seconds
            if (s.estimated_remaining != null) partial.estimated_remaining = s.estimated_remaining
            if (s.message           != null) partial.message           = s.message
            if (Object.keys(partial).length) setStatus(partial)
          },
        )
        wsRef.current = ws
        ws.onopen  = () => setBackendOk(true)
        ws.onerror = () => { setBackendOk(false) }
        ws.onclose = () => { if (active) setTimeout(connect, 3000) }
      } catch { setBackendOk(false) }
    }

    connect()
    return () => {
      active = false
      wsRef.current?.close()
      if (pollRef.current) clearInterval(pollRef.current)
    }
  }, [])

  /* ── Status polling (backup for WS) ──────────────────────────────────── */
  useEffect(() => {
    if (status.status === 'running' && backendOk) {
      if (pollRef.current) clearInterval(pollRef.current)
      pollRef.current = setInterval(async () => {
        try {
          const s = await api.getStatus()
          setStatus(s)
          if (s.status !== 'running') clearInterval(pollRef.current!)
        } catch {}
      }, 2000)
    }
    return () => { if (pollRef.current) clearInterval(pollRef.current) }
  }, [status.status, backendOk])

  /* ── Policy toggle ────────────────────────────────────────────────────── */
  const togglePolicy = (p: string) => {
    if (status.status === 'running') return
    const next = config.policies.includes(p)
      ? config.policies.filter(x => x !== p)
      : [...config.policies, p]
    if (next.length > 0) setConfig({ policies: next })
  }

  /* ── Run handler ──────────────────────────────────────────────────────── */
  const handleRun = async () => {
    if (!config.policies.length || status.status === 'running') return
    setLoading(true)
    setError(null)
    demoStopRef.current = false
    clearLogs()

    await checkBackend()

    if (backendOk) {
      /* ── Real backend run ──────────────────────────────────────────────── */
      addLog('🚀  Starting experiment...')
      addLog(`    Policies : ${config.policies.join(', ')}`)
      addLog(`    Workload : ${config.workload}  |  Duration: ${config.duration_seconds}s  |  Repeats: ${config.repeats}`)
      addLog('─'.repeat(52))
      try {
        const body = {
          policies:         config.policies,
          workload:         config.workload,
          duration_seconds: config.duration_seconds,
          repeats:          config.repeats,
          random_seed:      config.random_seed,
          run_name:         config.run_name || undefined,
        }
        const res = await api.runExperiment(body)
        if (res?.run_id) {
          setStatus({ status: 'running', run_id: res.run_id, message: 'Experiment running…' })
          addLog(`[API] Run started  id=${res.run_id}`)
        } else if (res?.detail) {
          throw new Error(res.detail)
        } else {
          throw new Error('Unexpected API response')
        }
      } catch (err: any) {
        const msg = err?.message ?? 'API error'
        setError(msg)
        addLog(`❌  ${msg}`)
        setStatus({ status: 'idle' })
      }
    } else {
      /* ── Demo / offline mode ───────────────────────────────────────────── */
      setStatus({ status: 'running', progress_pct: 0, message: 'Demo mode…' })
      await runDemoSimulation(
        config.policies,
        config.duration_seconds,
        config.repeats,
        addLog,
        setStatus,
        demoStopRef,
      )
    }

    setLoading(false)
  }

  /* ── Stop handler ─────────────────────────────────────────────────────── */
  const handleStop = async () => {
    demoStopRef.current = true
    if (backendOk) {
      try { await api.stopExperiment() } catch {}
    }
    addLog('⛔  Stop signal sent.')
    setStatus({ status: 'stopped', progress_pct: 0, current_policy: null, message: 'Stopped' })
    if (pollRef.current) clearInterval(pollRef.current)
  }

  /* ── Derived state ────────────────────────────────────────────────────── */
  const running  = status.status === 'running'
  const canRun   = !running && !loading && config.policies.length > 0
  const statusBadgeVariant: Record<string, 'blue'|'amber'|'green'|'red'|'dim'> = {
    idle: 'dim', running: 'amber', completed: 'green', failed: 'red', stopped: 'dim',
  }

  /* ── Render ───────────────────────────────────────────────────────────── */
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>

      {/* Backend status banner */}
      {backendOk === false && (
        <div style={{ background: 'rgba(245,158,11,0.08)', border: '1px solid rgba(245,158,11,0.25)', borderRadius: 8, padding: '8px 12px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span style={{ fontSize: 11, fontFamily: 'JetBrains Mono,monospace', color: '#f59e0b' }}>
            ⚠ Backend offline — demo mode active
          </span>
          <button onClick={checkBackend} style={{ fontSize: 10, fontFamily: 'JetBrains Mono,monospace', color: '#f59e0b', background: 'none', border: '1px solid rgba(245,158,11,0.3)', borderRadius: 6, padding: '2px 8px', cursor: 'pointer' }}>
            Retry
          </button>
        </div>
      )}
      {backendOk === true && (
        <div style={{ background: 'rgba(16,185,129,0.06)', border: '1px solid rgba(16,185,129,0.2)', borderRadius: 8, padding: '6px 12px', display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#10b981', display: 'inline-block' }} />
          <span style={{ fontSize: 11, fontFamily: 'JetBrains Mono,monospace', color: '#10b981' }}>Backend connected · localhost:8000</span>
        </div>
      )}

      {/* Error banner */}
      {error && (
        <div style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.25)', borderRadius: 8, padding: '8px 12px', fontSize: 11, fontFamily: 'JetBrains Mono,monospace', color: '#ef4444' }}>
          ❌ {error}
        </div>
      )}

      {/* Workload */}
      <div>
        <label style={S.label}>Workload Profile</label>
        <select style={S.input} value={config.workload}
          onChange={e => setConfig({ workload: e.target.value })} disabled={running}>
          {WORKLOADS.map(w => (
            <option key={w.value} value={w.value} style={{ background: '#141720' }}>{w.label}</option>
          ))}
        </select>
      </div>

      {/* Policies */}
      <div>
        <label style={S.label}>
          Policies to Compare
          <span style={{ marginLeft: 8, color: 'rgba(255,255,255,0.2)', textTransform: 'none', letterSpacing: 0 }}>
            — select one or more, then press Run
          </span>
        </label>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          {POLICIES.map(p => {
            const active = config.policies.includes(p)
            const color  = POLICY_COLORS[p]
            return (
              <button
                key={p}
                onClick={() => togglePolicy(p)}
                disabled={running}
                title={active ? `Remove ${p} from run` : `Add ${p} to run`}
                style={{
                  display: 'flex', alignItems: 'center', gap: 6,
                  padding: '6px 14px', borderRadius: 20, fontSize: 11,
                  fontFamily: 'JetBrains Mono,monospace',
                  cursor: running ? 'not-allowed' : 'pointer',
                  transition: 'all 0.15s',
                  fontWeight: active ? 700 : 400,
                  background: active ? `${color}18` : 'rgba(255,255,255,0.03)',
                  color:  active ? color : 'rgba(255,255,255,0.35)',
                  border: active ? `1px solid ${color}55` : '1px solid rgba(255,255,255,0.1)',
                  opacity: running ? 0.5 : 1,
                  boxShadow: active ? `0 0 12px ${color}18` : 'none',
                }}
              >
                {active && (
                  <CheckCircle2 size={12} style={{ flexShrink: 0 }} />
                )}
                {!active && (
                  <span style={{ width: 12, height: 12, borderRadius: '50%', border: '1px solid rgba(255,255,255,0.2)', display: 'inline-block', flexShrink: 0 }} />
                )}
                {p}
              </button>
            )
          })}
        </div>
        {config.policies.length > 0 && (
          <p style={{ fontSize: 10, fontFamily: 'JetBrains Mono,monospace', color: 'rgba(255,255,255,0.25)', marginTop: 6 }}>
            {config.policies.length} policy selected → press Run Experiment to start
          </p>
        )}
      </div>

      {/* Duration + Repeats */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
        <div>
          <label style={S.label}>Duration (s)</label>
          <input type="number" min={10} max={600} style={S.input}
            value={config.duration_seconds}
            onChange={e => setConfig({ duration_seconds: Math.max(10, parseInt(e.target.value) || 60) })}
            disabled={running} />
        </div>
        <div>
          <label style={S.label}>Repeats</label>
          <input type="number" min={1} max={5} style={S.input}
            value={config.repeats}
            onChange={e => setConfig({ repeats: Math.max(1, parseInt(e.target.value) || 1) })}
            disabled={running} />
        </div>
      </div>

      {/* Seed + Name */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
        <div>
          <label style={S.label}>Random Seed</label>
          <input type="number" style={S.input}
            value={config.random_seed}
            onChange={e => setConfig({ random_seed: parseInt(e.target.value) || 42 })}
            disabled={running} />
        </div>
        <div>
          <label style={S.label}>Run Name</label>
          <input type="text" placeholder="optional"
            style={{ ...S.input, color: config.run_name ? 'rgba(255,255,255,0.7)' : 'rgba(255,255,255,0.2)' }}
            value={config.run_name}
            onChange={e => setConfig({ run_name: e.target.value })}
            disabled={running} />
        </div>
      </div>

      {/* Buttons */}
      <div style={{ display: 'flex', gap: 10, paddingTop: 4 }}>
        <button
          className="btn btn-primary"
          onClick={handleRun}
          disabled={!canRun}
          style={{ opacity: canRun ? 1 : 0.4, cursor: canRun ? 'pointer' : 'not-allowed', minWidth: 160 }}
        >
          {loading || running ? <Spinner size={13} /> : <Play size={13} />}
          {running ? 'Running…' : 'Run Experiment'}
        </button>

        <button
          className="btn btn-danger"
          onClick={handleStop}
          disabled={!running && !loading}
          style={{ opacity: (running || loading) ? 1 : 0.3, cursor: (running || loading) ? 'pointer' : 'not-allowed' }}
        >
          <Square size={12} />
          Stop
        </button>

        <button
          className="btn btn-ghost"
          onClick={checkBackend}
          style={{ marginLeft: 'auto', padding: '8px 10px' }}
          title="Check backend connection"
        >
          <RefreshCw size={12} />
        </button>
      </div>

      {/* Status panel */}
      <div style={{ background: 'var(--bg-3)', borderRadius: 12, padding: 16, display: 'flex', flexDirection: 'column', gap: 10, border: '1px solid var(--border)' }}>
        <div style={S.row}>
          <span style={S.rowLabel}>Status</span>
          <Badge variant={statusBadgeVariant[status.status] ?? 'dim'}>
            {status.status.toUpperCase()}
          </Badge>
        </div>
        <div style={S.row}>
          <span style={S.rowLabel}>Current Policy</span>
          <span style={{ ...S.rowVal, color: status.current_policy ? POLICY_COLORS[status.current_policy] ?? '#fff' : 'rgba(255,255,255,0.3)' }}>
            {status.current_policy ?? '—'}
          </span>
        </div>
        <div style={S.row}>
          <span style={S.rowLabel}>Repeat</span>
          <span style={S.rowVal}>
            {status.total_repeats > 0 ? `${status.current_repeat + 1} / ${status.total_repeats}` : '—'}
          </span>
        </div>
        <div style={S.row}>
          <span style={S.rowLabel}>Elapsed</span>
          <span style={S.rowVal}>{status.elapsed_seconds > 0 ? `${status.elapsed_seconds}s` : '0s'}</span>
        </div>
        <div style={S.row}>
          <span style={S.rowLabel}>Progress</span>
          <span style={S.rowVal}>{status.progress_pct.toFixed(1)}%</span>
        </div>
        <ProgressBar value={status.progress_pct} shimmer={running} height={4} />
        {status.message && (
          <p style={{ fontSize: 11, fontFamily: 'JetBrains Mono,monospace', color: 'rgba(255,255,255,0.25)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {status.message}
          </p>
        )}
      </div>
    </div>
  )
}
