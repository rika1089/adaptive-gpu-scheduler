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
import { AGENT_COLORS, POLICY_COLORS, AGENT_DISPLAY_NAMES } from '@/lib/constants'

// Helper for smart unit conversion
const formatLatency = (ms: number) => {
  if (ms === 0) return '0ms'
  if (ms >= 1000) return `${(ms / 1000).toFixed(1)}s`
  return `${Math.round(ms)}ms`
}

// Fallback per-agent data from adaptive policy
const FALLBACK_AGENT = {
  coord:     { avg_latency_ms: 111900 },
  nlp:       { avg_latency_ms: 121200 },
  vision:    { avg_latency_ms: 128600 },
  reasoning: { avg_latency_ms: 91600 },
}

const FALLBACK_SUMMARY = {
  adaptive: { ...FALLBACK_AGENT, _fairness: 0.952 },
}

export default function MonitorPage() {
  const [summary, setSummary] = useState<any>(FALLBACK_SUMMARY)
  const [metrics, setMetrics] = useState<any[]>([])
  const [allocs, setAllocs]   = useState<any[]>([])
  const [loading, setLoading] = useState(false)

  const load = async () => {
    setLoading(true)
    try {
      const sum = await api.getSummary().catch(() => ({}))
      const met = await api.getAllMetrics('latest').catch(() => ({}))
      const alc = await api.getAllAllocations('latest').catch(() => ({}))

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

  const latestData = (() => {
    const data: Record<string, any> = { ...FALLBACK_AGENT }
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
      <div className="grid grid-cols-4 gap-3">
        {(['coord','nlp','vision','reasoning'] as const).map(agent => (
          <KpiCard
            key={agent}
            label={AGENT_DISPLAY_NAMES[agent] || agent}
            value={formatLatency(latestData[agent]?.avg_latency_ms || 0)}
            sub="live latency · adaptive"
            color={kpiColors[agent]}
          />
        ))}
      </div>

      <Card
        title="Latency Timeline — All Agents (Adaptive)"
        action={
          <>
            <ChartLegend items={(['coord','nlp','vision','reasoning'] as const).map(a => ({ label: AGENT_DISPLAY_NAMES[a] || a, color: AGENT_COLORS[a] }))} />
            <button onClick={load} className="ml-3 flex items-center gap-1 text-[11px] font-mono text-white/30 hover:text-white/60">
              {loading ? <Spinner className="w-3 h-3" /> : <RefreshCw size={11} />}
            </button>
          </>
        }
      >
        <LatencyLineChart rows={metrics.filter(r => r.policy === 'adaptive')} />
      </Card>

      <div className="grid grid-cols-2 gap-4">
        <Card
          title="SLA Violation Rate by Policy"
          action={<ChartLegend items={Object.keys(summary).map(p => ({ label: p, color: POLICY_COLORS[p] ?? '#8892a4' }))} />}
        >
          <SlaBarChart summary={summary} />
        </Card>

        <Card
          title="GPU Allocation Over Time — Adaptive"
          action={<ChartLegend items={(['coord','nlp','vision','reasoning'] as const).map(a => ({ label: AGENT_DISPLAY_NAMES[a] || a, color: AGENT_COLORS[a] }))} />}
        >
          <AllocationLineChart data={allocs.filter(r => r.policy === 'adaptive')} />
        </Card>
      </div>
    </div>
  )
}
