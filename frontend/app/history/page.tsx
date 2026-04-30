'use client'
import { useEffect, useState } from 'react'
import { Trash2, Clock, Play } from 'lucide-react'
import { api } from '@/lib/api'
import { Card } from '@/components/shared/Card'
import { Badge } from '@/components/shared/Badge'
import { EmptyState } from '@/components/shared/EmptyState'
import { POLICY_COLORS } from '@/lib/constants'

interface RunEntry {
  run_id: string; run_name: string; started_at: string; duration_seconds: number
  policies: string[]; workload: string; repeats: number; status: string
  has_results: boolean; summary_preview?: Record<string, any>
}

const SB: Record<string,'green'|'red'|'amber'|'dim'> = {
  completed:'green', failed:'red', stopped:'amber', running:'amber', idle:'dim'
}

export default function HistoryPage() {
  const [runs, setRuns] = useState<RunEntry[]>([])

  useEffect(() => {
    let local: RunEntry[] = []
    try { local = (JSON.parse(localStorage.getItem('gpu_run_history')||'[]') as RunEntry[]).reverse() } catch {}
    api.getRuns().then(remote => {
      const all = [...(remote as RunEntry[]), ...local]
        .filter((r,i,arr) => arr.findIndex(x=>x.run_id===r.run_id)===i)
      setRuns(all)
    }).catch(() => setRuns(local))
  }, [])

  const clear = () => {
    localStorage.removeItem('gpu_run_history')
    setRuns(prev => prev.filter(r => r.run_id === 'latest'))
  }

  return (
    <div className="animate-fade-in" style={{ maxWidth:900 }}>
      <Card
        title="Run History"
        action={runs.length > 0 ? (
          <button onClick={clear} style={{ display:'flex', alignItems:'center', gap:6, fontSize:11, fontFamily:'JetBrains Mono,monospace', color:'rgba(255,255,255,0.25)', background:'none', border:'none', cursor:'pointer' }}
            onMouseEnter={e=>(e.currentTarget.style.color='#ef4444')}
            onMouseLeave={e=>(e.currentTarget.style.color='rgba(255,255,255,0.25)')}>
            <Trash2 size={12}/> Clear local
          </button>
        ) : undefined}
      >
        {runs.length === 0 ? (
          <EmptyState message="No runs recorded yet. Run an experiment to see history here." />
        ) : (
          <div style={{ display:'flex', flexDirection:'column', gap:8 }}>
            {runs.map(run => (
              <div key={run.run_id} style={{ background:'var(--bg-3)', border:'1px solid var(--border)', borderRadius:12, padding:16, transition:'border-color 0.15s' }}
                onMouseEnter={e=>(e.currentTarget.style.borderColor='var(--border-strong)')}
                onMouseLeave={e=>(e.currentTarget.style.borderColor='var(--border)')}>
                <div style={{ display:'flex', alignItems:'flex-start', justifyContent:'space-between', gap:16 }}>
                  <div style={{ flex:1, minWidth:0 }}>
                    <div style={{ display:'flex', alignItems:'center', gap:8, marginBottom:6 }}>
                      <span style={{ fontSize:13, fontWeight:600, color:'rgba(255,255,255,0.8)', overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap' }}>{run.run_name||run.run_id}</span>
                      <span style={{ fontSize:10, fontFamily:'JetBrains Mono,monospace', color:'rgba(255,255,255,0.2)', flexShrink:0 }}>{run.run_id}</span>
                    </div>
                    <div style={{ display:'flex', flexWrap:'wrap', gap:'4px 16px', fontSize:11, fontFamily:'JetBrains Mono,monospace', color:'rgba(255,255,255,0.3)', marginBottom:8 }}>
                      <span style={{ display:'flex', alignItems:'center', gap:4 }}><Clock size={9}/>{run.started_at}</span>
                      <span>workload: {run.workload}</span>
                      <span>{run.duration_seconds}s</span>
                      <span>×{run.repeats}</span>
                    </div>
                    <div style={{ display:'flex', gap:6, flexWrap:'wrap', marginBottom: run.summary_preview ? 8 : 0 }}>
                      {run.policies?.map(p=>(
                        <span key={p} style={{ padding:'2px 8px', borderRadius:20, fontSize:10, fontFamily:'JetBrains Mono,monospace', background:`${POLICY_COLORS[p]??'#8892a4'}12`, color:POLICY_COLORS[p]??'#8892a4', border:`1px solid ${POLICY_COLORS[p]??'#8892a4'}25` }}>{p}</span>
                      ))}
                    </div>
                    {run.summary_preview&&(
                      <div style={{ display:'flex', gap:16, fontSize:10, fontFamily:'JetBrains Mono,monospace' }}>
                        {Object.entries(run.summary_preview || {}).map(([pol,d]:any)=>(
                          <span key={pol}>
                            <span style={{ color:POLICY_COLORS[pol]??'#8892a4' }}>{pol}:</span>
                            <span style={{ color:'rgba(255,255,255,0.3)', marginLeft:4 }}>
                              {d.coord_latency?`coord ${Math.round(d.coord_latency)}ms`:''}{d.fairness?` · J=${d.fairness.toFixed(3)}`:''}
                            </span>
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                  <div style={{ display:'flex', flexDirection:'column', alignItems:'flex-end', gap:8, flexShrink:0 }}>
                    <Badge variant={SB[run.status]??'dim'}>{run.status}</Badge>
                    {run.has_results&&(
                      <a href="/results" style={{ display:'flex', alignItems:'center', gap:4, fontSize:10, fontFamily:'JetBrains Mono,monospace', color:'#3b82f6', textDecoration:'none' }}>
                        <Play size={9}/>View results
                      </a>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  )
}
