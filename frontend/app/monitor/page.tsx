'use client'
import { useEffect, useState } from 'react'
import { RefreshCw } from 'lucide-react'
import { api } from '@/lib/api'
import { Card } from '@/components/shared/Card'
import { KpiCard } from '@/components/shared/KpiCard'
import { ChartLegend } from '@/components/shared/ChartLegend'
import { Spinner } from '@/components/shared/Spinner'
import { LatencyLineChart } from '@/components/charts/LatencyLineChart'
import { SlaBarChart } from '@/components/charts/SlaBarChart'
import { AllocationLineChart } from '@/components/charts/AllocationLineChart'
import { AGENT_COLORS, POLICY_COLORS } from '@/lib/constants'

// Fallback per-agent data from adaptive policy
const FALLBACK_AGENT = {
  coord:     { avg_latency_ms: 1139.62, avg_throughput: 56.929,  avg_gpu_share: 0.4305, avg_sla_violation: 0.9503 },
  nlp:       { avg_latency_ms: 1717.81, avg_throughput: 24.6757, avg_gpu_share: 0.1574, avg_sla_violation: 0.9618 },
  vision:    { avg_latency_ms: 1682.62, avg_throughput: 20.6537, avg_gpu_share: 0.1773, avg_sla_violation: 0.9341 },
  reasoning: { avg_latency_ms: 915.19,  avg_throughput: 15.794,  avg_gpu_share: 0.2348, avg_sla_violation: 0.9368 },
}

const FALLBACK_SUMMARY = {
  adaptive: { ...FALLBACK_AGENT, _fairness: 0.8972 },
  static: {
    coord:{ avg_latency_ms:1856.55,avg_throughput:43.8873,avg_gpu_share:0.25,avg_sla_violation:0.9502 },
    nlp:{ avg_latency_ms:613.34,avg_throughput:29.0063,avg_gpu_share:0.25,avg_sla_violation:0.8076 },
    vision:{ avg_latency_ms:1783.02,avg_throughput:23.2847,avg_gpu_share:0.25,avg_sla_violation:0.9671 },
    reasoning:{ avg_latency_ms:1301.96,avg_throughput:17.607,avg_gpu_share:0.25,avg_sla_violation:0.9876 },
    _fairness:1.0,
  },
  round_robin:{
    coord:{ avg_latency_ms:1566.94,avg_throughput:45.081,avg_gpu_share:0.2833,avg_sla_violation:0.8485 },
    nlp:{ avg_latency_ms:1075.4,avg_throughput:27.1157,avg_gpu_share:0.2833,avg_sla_violation:0.8238 },
    vision:{ avg_latency_ms:2748.41,avg_throughput:21.97,avg_gpu_share:0.2833,avg_sla_violation:0.9802 },
    reasoning:{ avg_latency_ms:1311.9,avg_throughput:16.1953,avg_gpu_share:0.15,avg_sla_violation:0.9799 },
    _fairness:0.6757,
  },
}

const FALLBACK_METRICS = [
  { elapsed_s:6,  policy:'adaptive', agent:'coord',     avg_latency_ms:923 },
  { elapsed_s:6,  policy:'adaptive', agent:'nlp',       avg_latency_ms:856 },
  { elapsed_s:6,  policy:'adaptive', agent:'vision',    avg_latency_ms:702 },
  { elapsed_s:6,  policy:'adaptive', agent:'reasoning', avg_latency_ms:377 },
  { elapsed_s:11, policy:'adaptive', agent:'coord',     avg_latency_ms:1100 },
  { elapsed_s:11, policy:'adaptive', agent:'nlp',       avg_latency_ms:1200 },
  { elapsed_s:11, policy:'adaptive', agent:'vision',    avg_latency_ms:1400 },
  { elapsed_s:11, policy:'adaptive', agent:'reasoning', avg_latency_ms:750 },
  { elapsed_s:16, policy:'adaptive', agent:'coord',     avg_latency_ms:1139 },
  { elapsed_s:16, policy:'adaptive', agent:'nlp',       avg_latency_ms:1717 },
  { elapsed_s:16, policy:'adaptive', agent:'vision',    avg_latency_ms:1682 },
  { elapsed_s:16, policy:'adaptive', agent:'reasoning', avg_latency_ms:915 },
]

const FALLBACK_ALLOC = [
  { elapsed_s:0,  policy:'adaptive', coord:0.4865, nlp:0.1467, vision:0.1467, reasoning:0.2201 },
  { elapsed_s:5,  policy:'adaptive', coord:0.3171, nlp:0.2029, vision:0.2155, reasoning:0.2645 },
  { elapsed_s:10, policy:'adaptive', coord:0.3184, nlp:0.1789, vision:0.2385, reasoning:0.2642 },
]

export default function MonitorPage() {
  const [summary, setSummary] = useState<any>(FALLBACK_SUMMARY)
  const [metrics, setMetrics] = useState<any[]>(FALLBACK_METRICS)
  const [allocs, setAllocs]   = useState<any[]>(FALLBACK_ALLOC)
  const [loading, setLoading] = useState(false)

  const load = async () => {
    setLoading(true)
    try {
      // Fetch data individually so one failure doesn't block the others
      const sum = await api.getSummary().catch(() => ({}))
      const met = await api.getAllMetrics('latest').catch(() => ({}))
      const alc = await api.getAllAllocations('latest').catch(() => ({}))

      // Normalise summary
      const norm: Record<string, any> = {}
      for (const [pol, data] of Object.entries(sum as any)) {
        norm[pol] = (data as any).agents ? { ...(data as any).agents, _fairness: (data as any).fairness } : data
      }
      if (Object.keys(norm).length) setSummary(norm)

      const allRows = Object.values(met as any).flat() as any[]
      if (allRows.length) setMetrics(allRows)

      const allocRows = Object.values(alc as any).flat() as any[]
      if (allocRows.length) setAllocs(allocRows)
    } catch (e) {
      console.error("Monitor load failed", e)
    }
    setLoading(false)
  }

  useEffect(() => {
    load()
    const timer = setInterval(load, 3000)
    return () => clearInterval(timer)
  }, [])

  // Get latest real-time data for KPI cards from the metrics array
  const latestData = (() => {
    const data = { ...FALLBACK_AGENT }
    metrics.forEach(m => {
      if (m.policy === 'adaptive' || !metrics.some(x => x.policy === 'adaptive')) {
        data[m.agent] = { avg_latency_ms: m.avg_latency_ms }
      }
    })
    return data
  })()

  const kpiColors: Record<string, 'blue'|'green'|'amber'|'purple'> = {
    coord:'blue', nlp:'green', vision:'purple', reasoning:'amber'
  }

  return (
    <div className="space-y-5 animate-fade-in">
      {/* Per-agent KPI row */}
      <div className="grid grid-cols-4 gap-3">
        {(['coord','nlp','vision','reasoning'] as const).map(agent => (
          <KpiCard
            key={agent}
            label={agent}
            value={`${Math.round(latestData[agent]?.avg_latency_ms || 0)}ms`}
            sub="live latency · adaptive"
            color={kpiColors[agent]}
          />
        ))}
      </div>

      {/* Latency timeline */}
      <Card
        title="Latency Timeline — All Agents (Adaptive)"
        action={
          <>
            <ChartLegend items={(['coord','nlp','vision','reasoning'] as const).map(a => ({ label: a, color: AGENT_COLORS[a] }))} />
            <button onClick={load} className="ml-3 flex items-center gap-1 text-[11px] font-mono text-white/30 hover:text-white/60">
              {loading ? <Spinner className="w-3 h-3" /> : <RefreshCw size={11} />}
            </button>
          </>
        }
      >
        <LatencyLineChart rows={metrics.filter(r => r.policy === 'adaptive')} />
      </Card>

      <div className="grid grid-cols-2 gap-4">
        {/* SLA comparison */}
        <Card
          title="SLA Violation Rate by Policy"
          action={<ChartLegend items={Object.keys(summary).map(p => ({ label: p, color: POLICY_COLORS[p] ?? '#8892a4' }))} />}
        >
          <SlaBarChart summary={summary} />
        </Card>

        {/* Allocation over time */}
        <Card
          title="GPU Allocation Over Time — Adaptive"
          action={<ChartLegend items={(['coord','nlp','vision','reasoning'] as const).map(a => ({ label: a, color: AGENT_COLORS[a] }))} />}
        >
          <AllocationLineChart data={allocs.filter(r => r.policy === 'adaptive')} />
        </Card>
      </div>
    </div>
  )
}
