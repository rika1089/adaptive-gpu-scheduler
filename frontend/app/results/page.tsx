'use client'
import { useEffect, useState } from 'react'
import { Download, RefreshCw } from 'lucide-react'
import { api } from '@/lib/api'
import { Card } from '@/components/shared/Card'
import { ChartLegend } from '@/components/shared/ChartLegend'
import { Spinner } from '@/components/shared/Spinner'
import { AgentDrilldown } from '@/components/dashboard/AgentDrilldown'
import { PolicyComparisonTable } from '@/components/dashboard/PolicyComparisonTable'
import { GpuShareChart } from '@/components/charts/GpuShareChart'
import { AllocationLineChart } from '@/components/charts/AllocationLineChart'
import { POLICY_COLORS, AGENT_COLORS } from '@/lib/constants'

export default function ResultsPage() {
  const [summary, setSummary] = useState<Record<string,any>>({})
  const [allocs, setAllocs]   = useState<any[]>([])
  const [active, setActive]   = useState('adaptive')
  const [files, setFiles]     = useState<{csvs:string[];reports:string[];figures:string[]}>({csvs:[],reports:[],figures:[]})
  const [loading, setLoading] = useState(false)

  const load = async () => {
    setLoading(true)
    try {
      const sum = await api.getSummary().catch(() => ({}))
      const alc = await api.getAllAllocations('latest').catch(() => ({}))
      const fs  = await api.getFiles().catch(() => ({csvs:[],reports:[],figures:[]}))

      const norm: Record<string,any> = {}
      for (const [pol, d] of Object.entries(sum as any)) {
        norm[pol] = (d as any).agents ? {...(d as any).agents, _fairness:(d as any).fairness} : d
      }
      if (Object.keys(norm).length) setSummary(norm)
      
      const rows = Object.values(alc as any).flat() as any[]
      if (rows.length) setAllocs(rows)
      setFiles(fs as any)
    } catch {}
    setLoading(false)
  }

  useEffect(() => {
    load()
    const timer = setInterval(load, 5000) // Poll every 5s
    return () => clearInterval(timer)
  }, [])

  const policies = Object.keys(summary)
  const btnStyle = (p: string): React.CSSProperties => {
    const color = POLICY_COLORS[p] ?? '#8892a4'
    const isActive = active === p
    return { padding:'5px 12px', borderRadius:20, fontSize:11, fontFamily:'JetBrains Mono,monospace', cursor:'pointer', border: isActive?`1px solid ${color}44`:'1px solid var(--border)', background: isActive?`${color}12`:'transparent', color: isActive?color:'rgba(255,255,255,0.3)', transition:'all 0.15s' }
  }

  return (
    <div className="animate-fade-in" style={{ display:'flex', flexDirection:'column', gap:16 }}>
      
      {policies.length === 0 && !loading && (
        <Card title="No Results Found">
          <div style={{ padding:'40px 20px', textAlign:'center', color:'rgba(255,255,255,0.4)' }}>
            <p>No experiment results found. Please run an experiment first to see analytics here.</p>
          </div>
        </Card>
      )}

      {/* Policy tabs + downloads */}
      {policies.length > 0 && (
      <>
        <div style={{ display:'flex', alignItems:'center', gap:10, flexWrap:'wrap' }}>
          <span style={{ fontSize:11, fontFamily:'JetBrains Mono,monospace', color:'rgba(255,255,255,0.3)' }}>Viewing:</span>
          {policies.map(p=><button key={p} onClick={()=>setActive(p)} style={btnStyle(p)}>{p}</button>)}
          <div style={{ marginLeft:'auto', display:'flex', gap:8 }}>
            <button onClick={load} className="btn btn-ghost" style={{ padding:'5px 10px', fontSize:11 }}>
              {loading ? <Spinner size={12}/> : <RefreshCw size={12}/>} Reload
            </button>
            <a href={api.downloadUrl('report','comparison_summary.json')} target="_blank" className="btn btn-ghost" style={{ padding:'5px 10px', fontSize:11, textDecoration:'none' }}>
              <Download size={12}/> JSON
            </a>
            <a href={api.downloadUrl('csv',`${active}_repeat0_metrics.csv`)} target="_blank" className="btn btn-ghost" style={{ padding:'5px 10px', fontSize:11, textDecoration:'none' }}>
              <Download size={12}/> CSV
            </a>
          </div>
        </div>

        {/* Agent drill-down */}
        <Card title={`Agent Metrics — ${active}`}>
          <AgentDrilldown summary={summary} policy={active}/>
        </Card>

        {/* Comparison matrix */}
        <Card title="Policy Comparison Matrix">
          <PolicyComparisonTable summary={summary}/>
        </Card>

        {/* Charts */}
        <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:16 }}>
          <Card title={`GPU Share Distribution — ${active}`}
            action={<ChartLegend items={(['coord','nlp','vision','reasoning'] as const).map(a=>({label:a,color:AGENT_COLORS[a]}))}/>}>
            <GpuShareChart summary={summary} policy={active}/>
          </Card>
          <Card title="Allocation Over Time — Adaptive"
            action={<ChartLegend items={(['coord','nlp','vision','reasoning'] as const).map(a=>({label:a,color:AGENT_COLORS[a]}))}/>}>
            <AllocationLineChart data={allocs.filter(r=>r.policy==='adaptive')}/>
          </Card>
        </div>
      </>
      )}

      {/* Downloadable artifacts */}
      {policies.length > 0 && (files.csvs?.length>0||files.reports?.length>0) && (
        <Card title="Downloadable Artifacts">
          <div style={{ display:'grid', gridTemplateColumns:'repeat(3,1fr)', gap:8 }}>
            {files.csvs?.map(f=>(
              <a key={f} href={api.downloadUrl('csv',f)} target="_blank"
                style={{ display:'flex', alignItems:'center', gap:6, padding:'8px 10px', borderRadius:8, background:'var(--bg-3)', border:'1px solid var(--border)', fontSize:11, fontFamily:'JetBrains Mono,monospace', color:'#3b82f6', textDecoration:'none', overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap' }}>
                <Download size={11}/>{f}
              </a>
            ))}
            {files.reports?.map(f=>(
              <a key={f} href={api.downloadUrl('report',f)} target="_blank"
                style={{ display:'flex', alignItems:'center', gap:6, padding:'8px 10px', borderRadius:8, background:'var(--bg-3)', border:'1px solid var(--border)', fontSize:11, fontFamily:'JetBrains Mono,monospace', color:'#10b981', textDecoration:'none', overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap' }}>
                <Download size={11}/>{f}
              </a>
            ))}
          </div>
        </Card>
      )}
    </div>
  )
}
