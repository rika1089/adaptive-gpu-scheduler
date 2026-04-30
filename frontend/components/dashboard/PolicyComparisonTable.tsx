'use client'
import { AGENTS, POLICY_COLORS, AGENT_COLORS } from '@/lib/constants'

interface Props { summary: Record<string, any> }

export function PolicyComparisonTable({ summary }: Props) {
  const policies = Object.keys(summary)
  const maxLat = Math.max(...AGENTS.flatMap(a => policies.map(p => summary[p]?.[a]?.avg_latency_ms ?? 0)))
  const maxThr = Math.max(...AGENTS.flatMap(a => policies.map(p => summary[p]?.[a]?.avg_throughput ?? 0)))
  const th: React.CSSProperties = { textAlign:'left', paddingBottom:12, fontSize:10, fontFamily:'JetBrains Mono,monospace', color:'rgba(255,255,255,0.2)', textTransform:'uppercase', letterSpacing:'0.08em', fontWeight:400, paddingRight:16, borderBottom:'1px solid var(--border)' }
  const td: React.CSSProperties = { padding:'7px 16px 7px 0', borderBottom:'1px solid rgba(255,255,255,0.04)', verticalAlign:'middle' }

  return (
    <div style={{ overflowX:'auto' }}>
      <table style={{ width:'100%', borderCollapse:'collapse', fontSize:12 }}>
        <thead>
          <tr>
            <th style={th}>Agent</th><th style={th}>Policy</th><th style={th}>Avg Latency</th>
            <th style={th}>Throughput</th><th style={th}>GPU Share</th><th style={th}>SLA Viol.</th>
          </tr>
        </thead>
        <tbody>
          {AGENTS.flatMap((agent,ai) =>
            policies.map((policy,pi) => {
              const d = summary[policy]?.[agent] ?? {}
              const lat   = d.avg_latency_ms ?? 0
              const thr   = d.avg_throughput ?? 0
              const share = d.avg_gpu_share ?? 0
              const sla   = d.avg_sla_violation ?? 0
              const sc    = sla > 0.9 ? '#ef4444' : sla > 0.8 ? '#f59e0b' : '#10b981'
              return (
                <tr key={`${agent}-${policy}`}>
                  {pi===0 && (
                    <td rowSpan={policies.length} style={{ ...td, paddingRight:16 }}>
                      <div style={{ display:'flex', alignItems:'center', gap:7 }}>
                        <span style={{ width:7, height:7, borderRadius:'50%', background:AGENT_COLORS[agent], display:'inline-block', flexShrink:0 }}/>
                        <span style={{ fontFamily:'JetBrains Mono,monospace', fontSize:11, color:'rgba(255,255,255,0.65)' }}>{agent}</span>
                      </div>
                    </td>
                  )}
                  <td style={td}><span style={{ fontFamily:'JetBrains Mono,monospace', fontSize:11, color:POLICY_COLORS[policy]??'#8892a4' }}>{policy}</span></td>
                  <td style={td}>
                    <div style={{ display:'flex', alignItems:'center', gap:8 }}>
                      <div style={{ width:56, height:3, borderRadius:2, background:'rgba(255,255,255,0.05)', overflow:'hidden' }}>
                        <div style={{ height:'100%', borderRadius:2, width:`${(lat/maxLat)*100}%`, background:POLICY_COLORS[policy]??'#8892a4', opacity:0.6 }}/>
                      </div>
                      <span style={{ fontFamily:'JetBrains Mono,monospace', fontSize:11, color:'rgba(255,255,255,0.55)' }}>{Math.round(lat)}ms</span>
                    </div>
                  </td>
                  <td style={td}>
                    <div style={{ display:'flex', alignItems:'center', gap:8 }}>
                      <div style={{ width:40, height:3, borderRadius:2, background:'rgba(255,255,255,0.05)', overflow:'hidden' }}>
                        <div style={{ height:'100%', borderRadius:2, width:`${(thr/maxThr)*100}%`, background:POLICY_COLORS[policy]??'#8892a4', opacity:0.6 }}/>
                      </div>
                      <span style={{ fontFamily:'JetBrains Mono,monospace', fontSize:11, color:'rgba(255,255,255,0.55)' }}>{thr.toFixed(2)}</span>
                    </div>
                  </td>
                  <td style={td}><span style={{ fontFamily:'JetBrains Mono,monospace', fontSize:11, color:'rgba(255,255,255,0.55)' }}>{(share*100).toFixed(1)}%</span></td>
                  <td style={td}><span style={{ fontFamily:'JetBrains Mono,monospace', fontSize:11, fontWeight:600, color:sc }}>{(sla*100).toFixed(1)}%</span></td>
                </tr>
              )
            })
          )}
        </tbody>
      </table>
    </div>
  )
}
