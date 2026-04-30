'use client'
import { AGENTS, AGENT_COLORS } from '@/lib/constants'
import { ProgressBar } from '@/components/shared/ProgressBar'

interface Props {
  summary: Record<string, any>
  policy: string
}

export function AgentDrilldown({ summary, policy }: Props) {
  const pData = summary[policy] ?? {}

  return (
    <div className="grid grid-cols-4 gap-3">
      {AGENTS.map(agent => {
        const d = pData[agent] ?? {}
        const latency  = d.avg_latency_ms  ?? 0
        const thr      = d.avg_throughput  ?? 0
        const share    = d.avg_gpu_share   ?? 0
        const sla      = d.avg_sla_violation ?? 0
        const color    = AGENT_COLORS[agent]
        const slaColor = sla > 0.9 ? '#ef4444' : sla > 0.8 ? '#f59e0b' : '#10b981'

        return (
          <div
            key={agent}
            className="rounded-xl p-3.5 border transition-all duration-200"
            style={{ background: `${color}08`, borderColor: `${color}22` }}
          >
            <p className="text-[10px] font-mono font-bold uppercase tracking-widest mb-3" style={{ color }}>
              {agent}
            </p>

            <div className="space-y-2.5">
              <Row label="Latency" value={`${Math.round(latency)}ms`} color={color} />
              <Row label="Throughput" value={`${thr.toFixed(2)} r/s`} color={color} />
              <Row label="GPU Share" value={`${(share * 100).toFixed(1)}%`} color={color} />
              <Row label="SLA Viol." value={`${(sla * 100).toFixed(1)}%`} color={slaColor} />
            </div>

            <div className="mt-3">
              <ProgressBar value={share * 100} color={color} height={3} />
            </div>
          </div>
        )
      })}
    </div>
  )
}

function Row({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div className="flex justify-between items-center">
      <span className="text-[10px] text-white/30">{label}</span>
      <span className="text-[11px] font-mono font-semibold" style={{ color }}>{value}</span>
    </div>
  )
}
