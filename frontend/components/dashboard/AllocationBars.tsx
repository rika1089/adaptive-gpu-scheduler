'use client'
import { AGENTS, AGENT_COLORS, POLICY_COLORS } from '@/lib/constants'

interface Props {
  summary: Record<string, any>
}

export function AllocationBars({ summary }: Props) {
  return (
    <div className="space-y-4">
      {Object.keys(summary).map(policy => {
        const pData = summary[policy]
        const shares = AGENTS.map(a => ({
          agent: a,
          share: pData?.[a]?.avg_gpu_share ?? 0,
          color: AGENT_COLORS[a],
        }))
        const fairness = pData?._fairness ?? 0

        return (
          <div key={policy}>
            <div className="flex justify-between items-center mb-1.5">
              <span className="text-[11px] font-mono font-semibold" style={{ color: POLICY_COLORS[policy] }}>
                {policy}
              </span>
              <span className="text-[10px] font-mono text-white/30">
                fairness: {fairness.toFixed(4)}
              </span>
            </div>
            {/* Stacked bar */}
            <div className="flex h-5 rounded overflow-hidden gap-px">
              {shares.map(({ agent, share, color }) => (
                <div
                  key={agent}
                  className="flex items-center justify-center transition-all duration-500 text-[9px] font-mono font-bold text-white/80"
                  style={{ flex: share, background: color, minWidth: share > 0 ? 4 : 0 }}
                  title={`${agent}: ${(share * 100).toFixed(1)}%`}
                >
                  {share * 100 > 12 ? `${(share * 100).toFixed(0)}%` : ''}
                </div>
              ))}
            </div>
            {/* Legend */}
            <div className="flex gap-3 mt-1.5">
              {shares.map(({ agent, share, color }) => (
                <span key={agent} className="text-[10px] font-mono flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full" style={{ background: color }} />
                  <span style={{ color }}>{agent[0].toUpperCase()}: {(share * 100).toFixed(0)}%</span>
                </span>
              ))}
            </div>
          </div>
        )
      })}
    </div>
  )
}
