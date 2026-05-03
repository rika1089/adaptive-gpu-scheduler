'use client'
import { useEffect, useState, useMemo } from 'react'
import { RefreshCw } from 'lucide-react'
import { api } from '@/lib/api'
import { KpiCard } from '@/components/shared/KpiCard'
import { Card } from '@/components/shared/Card'
import { ChartLegend } from '@/components/shared/ChartLegend'
import { Spinner } from '@/components/shared/Spinner'
import { LatencyBarChart } from '@/components/charts/LatencyBarChart'
import { ThroughputBarChart } from '@/components/charts/ThroughputBarChart'
import { CostPerformanceChart } from '@/components/charts/CostPerformanceChart'
import { AllocationBars } from '@/components/dashboard/AllocationBars'
import { FairnessGauge } from '@/components/dashboard/FairnessGauge'
import { POLICY_COLORS } from '@/lib/constants'

// Helper for smart unit conversion
const formatLatency = (ms: number) => {
  if (ms === 0) return '0ms'
  if (ms >= 1000) return `${(ms / 1000).toFixed(2)}s`
  return `${ms.toFixed(0)}ms`
}

// Embedded fallback
const FALLBACK = {
  adaptive: {
    coord:     { avg_latency_ms: 111900, avg_throughput: 19.8,  avg_gpu_share: 0.15, avg_sla_violation: 1.0 },
    nlp:       { avg_latency_ms: 121200, avg_throughput: 15.1,  avg_gpu_share: 0.28, avg_sla_violation: 1.0 },
    vision:    { avg_latency_ms: 128600, avg_throughput: 12.4,  avg_gpu_share: 0.24, avg_sla_violation: 1.0 },
    reasoning: { avg_latency_ms: 91600,  avg_throughput: 10.8,  avg_gpu_share: 0.33, avg_sla_violation: 1.0 },
    _fairness: 0.952,
  },
}

export default function Overview() {
  const [summary, setSummary] = useState<Record<string, any>>(FALLBACK)
  const [loading, setLoading] = useState(false)

  const load = async () => {
    setLoading(true)
    try {
      const raw = await api.getSummary()
      const normalised: Record<string, any> = {}
      for (const [pol, data] of Object.entries(raw as Record<string, any>)) {
        if (data.agents) {
          normalised[pol] = { ...data.agents, _fairness: data.fairness ?? 1 }
        } else {
          normalised[pol] = data
        }
      }
      if (Object.keys(normalised).length > 0) {
        setSummary(normalised)
      }
    } catch (e) {
      console.warn("Failed to fetch real summary, using fallback", e)
    }
    setLoading(false)
  }

  useEffect(() => { load() }, [])

  // Calculate dynamic KPIs
  const kpis = useMemo(() => {
    let bestLatency = Infinity
    let bestLatAgent = ''
    let bestLatPolicy = ''
    
    let peakThroughput = 0
    let peakThrAgent = ''
    let peakThrPolicy = ''

    let bestFairness = 0
    let bestFairPolicy = ''

    const policies = Object.keys(summary)
    
    policies.forEach(pol => {
      const data = summary[pol]
      const agents = { ...data }
      delete agents._fairness
      
      const fairness = data._fairness ?? 0
      if (fairness > bestFairness) {
        bestFairness = fairness
        bestFairPolicy = pol
      }

      Object.entries(agents).forEach(([agent, metrics]: [string, any]) => {
        if (!metrics || typeof metrics !== 'object') return
        
        const lat = metrics.avg_latency_ms
        const thr = metrics.avg_throughput

        if (lat < bestLatency && lat > 0) {
          bestLatency = lat
          bestLatAgent = agent
          bestLatPolicy = pol
        }

        if (thr > peakThroughput) {
          peakThroughput = thr
          peakThrAgent = agent
          peakThrPolicy = pol
        }
      })
    })

    return {
      bestLatency: bestLatency === Infinity ? '0ms' : formatLatency(bestLatency),
      bestLatSub: bestLatAgent ? `${bestLatPolicy} · ${bestLatAgent}` : 'no data',
      peakThroughput: peakThroughput.toFixed(1),
      peakThrSub: peakThrAgent ? `${peakThrPolicy} · ${peakThrAgent}` : 'no data',
      fairness: bestFairness.toFixed(3),
      fairnessSub: bestFairPolicy ? `${bestFairPolicy} policy` : 'no data',
      policiesCount: policies.length,
      agentsCount: policies.length > 0 ? Object.keys(summary[policies[0]]).filter(k => k !== '_fairness').length : 0
    }
  }, [summary])

  const legendItems = Object.keys(summary).map(p => ({ label: p, color: POLICY_COLORS[p] ?? '#8892a4' }))

  return (
    <div className="space-y-5 animate-fade-in">
      {/* KPI Row */}
      <div className="grid grid-cols-5 gap-3">
        <KpiCard label="Best Latency"   value={kpis.bestLatency}    sub={kpis.bestLatSub} color="blue" />
        <KpiCard label="Peak Throughput" value={kpis.peakThroughput} sub={kpis.peakThrSub} color="green" />
        <KpiCard label="Jain Fairness"  value={kpis.fairness}       sub={kpis.fairnessSub} color="amber" />
        <KpiCard label="Policies Run"   value={String(kpis.policiesCount)} sub="Active in comparison" color="purple" />
        <KpiCard label="Agents Active"  value={String(kpis.agentsCount)}   sub="Heterogeneous models" color="cyan" />
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-2 gap-4">
        <Card
          title="Avg Latency"
          action={<ChartLegend items={legendItems} />}
        >
          <LatencyBarChart summary={summary} />
        </Card>
        <Card
          title="Throughput · req/s"
          action={<ChartLegend items={legendItems} />}
        >
          <ThroughputBarChart summary={summary} />
        </Card>
      </div>

      {/* Trade-off row */}
      <div className="grid grid-cols-1">
        <Card title="Cost-Performance Trade-off (Paper Figure 2d)">
          <CostPerformanceChart summary={summary} />
        </Card>
      </div>

      {/* Allocation + Fairness */}
      <div className="grid grid-cols-2 gap-4">
        <Card title="GPU Allocation by Policy">
          <AllocationBars summary={summary} />
        </Card>
        <Card
          title="Jain Fairness Index"
          action={
            <button onClick={load} className="flex items-center gap-1.5 text-[11px] font-mono text-white/30 hover:text-white/60 transition-colors">
              {loading ? <Spinner className="w-3 h-3" /> : <RefreshCw size={12} />}
              Refresh
            </button>
          }
        >
          <div className="flex justify-around pt-2">
            {Object.entries(summary).map(([pol, data]) => (
              <FairnessGauge key={pol} policy={pol} value={(data as any)._fairness ?? 1} />
            ))}
          </div>
        </Card>
      </div>
    </div>
  )
}
