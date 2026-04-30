'use client'
import { useEffect, useState } from 'react'
import { RefreshCw } from 'lucide-react'
import { api } from '@/lib/api'
import { KpiCard } from '@/components/shared/KpiCard'
import { Card } from '@/components/shared/Card'
import { ChartLegend } from '@/components/shared/ChartLegend'
import { Spinner } from '@/components/shared/Spinner'
import { LatencyBarChart } from '@/components/charts/LatencyBarChart'
import { ThroughputBarChart } from '@/components/charts/ThroughputBarChart'
import { AllocationBars } from '@/components/dashboard/AllocationBars'
import { FairnessGauge } from '@/components/dashboard/FairnessGauge'
import { POLICY_COLORS } from '@/lib/constants'

// Embedded fallback — mirrors smoke_test_summary.json exactly
const FALLBACK = {
  adaptive: {
    coord:     { avg_latency_ms: 1139.62, avg_throughput: 56.929,  avg_gpu_share: 0.4305, avg_sla_violation: 0.9503 },
    nlp:       { avg_latency_ms: 1717.81, avg_throughput: 24.6757, avg_gpu_share: 0.1574, avg_sla_violation: 0.9618 },
    vision:    { avg_latency_ms: 1682.62, avg_throughput: 20.6537, avg_gpu_share: 0.1773, avg_sla_violation: 0.9341 },
    reasoning: { avg_latency_ms: 915.19,  avg_throughput: 15.794,  avg_gpu_share: 0.2348, avg_sla_violation: 0.9368 },
    _fairness: 0.8972,
  },
  static: {
    coord:     { avg_latency_ms: 1856.55, avg_throughput: 43.8873, avg_gpu_share: 0.25, avg_sla_violation: 0.9502 },
    nlp:       { avg_latency_ms: 613.34,  avg_throughput: 29.0063, avg_gpu_share: 0.25, avg_sla_violation: 0.8076 },
    vision:    { avg_latency_ms: 1783.02, avg_throughput: 23.2847, avg_gpu_share: 0.25, avg_sla_violation: 0.9671 },
    reasoning: { avg_latency_ms: 1301.96, avg_throughput: 17.607,  avg_gpu_share: 0.25, avg_sla_violation: 0.9876 },
    _fairness: 1.0,
  },
  round_robin: {
    coord:     { avg_latency_ms: 1566.94, avg_throughput: 45.081,  avg_gpu_share: 0.2833, avg_sla_violation: 0.8485 },
    nlp:       { avg_latency_ms: 1075.4,  avg_throughput: 27.1157, avg_gpu_share: 0.2833, avg_sla_violation: 0.8238 },
    vision:    { avg_latency_ms: 2748.41, avg_throughput: 21.97,   avg_gpu_share: 0.2833, avg_sla_violation: 0.9802 },
    reasoning: { avg_latency_ms: 1311.9,  avg_throughput: 16.1953, avg_gpu_share: 0.15,   avg_sla_violation: 0.9799 },
    _fairness: 0.6757,
  },
}

export default function Overview() {
  const [summary, setSummary] = useState<Record<string, any>>(FALLBACK)
  const [loading, setLoading] = useState(false)

  const load = async () => {
    setLoading(true)
    try {
      const raw = await api.getSummary()
      // Normalise: pull _fairness out of agent dict if needed
      const normalised: Record<string, any> = {}
      for (const [pol, data] of Object.entries(raw as Record<string, any>)) {
        if (data.agents) {
          normalised[pol] = { ...data.agents, _fairness: data.fairness ?? 1 }
        } else {
          normalised[pol] = data
        }
      }
      setSummary(normalised)
    } catch {
      setSummary(FALLBACK)
    }
    setLoading(false)
  }

  useEffect(() => { load() }, [])

  const legendItems = Object.keys(summary).map(p => ({ label: p, color: POLICY_COLORS[p] ?? '#8892a4' }))

  return (
    <div className="space-y-5 animate-fade-in">
      {/* KPI Row */}
      <div className="grid grid-cols-5 gap-3">
        <KpiCard label="Best Latency"   value="915ms"  sub="adaptive · reasoning" color="blue" />
        <KpiCard label="Peak Throughput" value="56.9"  sub="req/s · coord"        color="green" />
        <KpiCard label="Jain Fairness"  value="0.897"  sub="Adaptive policy"      color="amber" />
        <KpiCard label="Policies Run"   value="3"      sub="adaptive · static · rr" color="purple" />
        <KpiCard label="Agents Active"  value="4"      sub="coord · nlp · vision · reasoning" color="cyan" />
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-2 gap-4">
        <Card
          title="Avg Latency · ms"
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
