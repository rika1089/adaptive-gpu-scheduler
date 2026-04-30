'use client'
import { useState, useEffect } from 'react'
import { Save, CheckCircle } from 'lucide-react'
import { Card } from '@/components/shared/Card'

interface Settings { apiUrl: string; wsUrl: string }
const DEFAULT: Settings = { apiUrl:'http://localhost:8000', wsUrl:'ws://localhost:8000/ws/logs' }

export default function SettingsPage() {
  const [s, setS] = useState<Settings>(DEFAULT)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    try { setS(JSON.parse(localStorage.getItem('gpu_settings')||'null')??DEFAULT) } catch {}
  }, [])

  const save = () => {
    localStorage.setItem('gpu_settings', JSON.stringify(s))
    setSaved(true)
    setTimeout(()=>setSaved(false), 2000)
  }

  const iStyle = { width:'100%', background:'var(--bg-3)', border:'1px solid var(--border)', borderRadius:8, padding:'7px 12px', fontSize:12, fontFamily:'JetBrains Mono,monospace', color:'rgba(255,255,255,0.7)', outline:'none' }

  return (
    <div className="animate-fade-in" style={{ display:'flex', flexDirection:'column', gap:14, maxWidth:620 }}>

      <Card title="Backend Connection">
        <div style={{ display:'flex', flexDirection:'column', gap:14 }}>
          {[
            { label:'API Base URL',  key:'apiUrl',  ph:'http://localhost:8000' },
            { label:'WebSocket URL', key:'wsUrl',   ph:'ws://localhost:8000/ws/logs' },
          ].map(({label,key,ph})=>(
            <div key={key}>
              <label style={{ fontSize:10, fontFamily:'JetBrains Mono,monospace', color:'rgba(255,255,255,0.3)', textTransform:'uppercase', letterSpacing:'0.08em', display:'block', marginBottom:5 }}>{label}</label>
              <input style={iStyle} value={(s as any)[key]} placeholder={ph}
                onChange={e=>setS(prev=>({...prev,[key]:e.target.value}))} />
            </div>
          ))}
          <button className="btn btn-primary" onClick={save} style={{ alignSelf:'flex-start' }}>
            {saved ? <CheckCircle size={14}/> : <Save size={14}/>}
            {saved ? 'Saved!' : 'Save Settings'}
          </button>
        </div>
      </Card>

      <Card title="Output Folder Mapping">
        {[
          { label:'Metrics Dir',  val:'output/metrics/', desc:'CSV files per policy per repeat'  },
          { label:'Figures Dir',  val:'output/figures/', desc:'PNG bar charts'                   },
          { label:'Reports Dir',  val:'output/reports/', desc:'comparison_summary.json'          },
          { label:'Logs Dir',     val:'output/logs/',    desc:'DGX vLLM server logs'             },
        ].map(({label,val,desc},i,arr)=>(
          <div key={label} style={{ display:'flex', justifyContent:'space-between', alignItems:'flex-start', gap:16, paddingBottom:i<arr.length-1?12:0, marginBottom:i<arr.length-1?12:0, borderBottom: i<arr.length-1?'1px solid var(--border)':'none' }}>
            <div>
              <p style={{ fontSize:12, fontFamily:'JetBrains Mono,monospace', color:'rgba(255,255,255,0.6)', marginBottom:2 }}>{label}</p>
              <p style={{ fontSize:11, color:'rgba(255,255,255,0.25)' }}>{desc}</p>
            </div>
            <code style={{ fontSize:11, fontFamily:'JetBrains Mono,monospace', color:'#3b82f6', background:'rgba(59,130,246,0.08)', padding:'2px 8px', borderRadius:6, flexShrink:0 }}>{val}</code>
          </div>
        ))}
        <p style={{ fontSize:11, fontFamily:'JetBrains Mono,monospace', color:'rgba(255,255,255,0.2)', marginTop:12, background:'var(--bg-3)', borderRadius:8, padding:'8px 12px', border:'1px solid var(--border)' }}>
          Paths relative to adaptive-gpu-paper/ root. FastAPI parser reads these automatically.
        </p>
      </Card>

      <Card title="Backend Start Commands">
        {[
          { label:'Start FastAPI backend', cmd:'cd adaptive-gpu-paper/backend && uvicorn app.main:app --reload --port 8000' },
          { label:'Quick smoke test',      cmd:'cd adaptive-gpu-paper && bash scripts/run_simulation.sh --quick'           },
          { label:'Full paper run',        cmd:'cd adaptive-gpu-paper && bash scripts/run_simulation.sh'                   },
          { label:'Launch DGX vLLM',       cmd:'cd adaptive-gpu-paper && bash scripts/launch_all.sh'                       },
        ].map(({label,cmd})=>(
          <div key={cmd} style={{ background:'#050709', borderRadius:8, border:'1px solid var(--border)', padding:12, marginBottom:8 }}>
            <p style={{ fontSize:10, color:'rgba(255,255,255,0.25)', marginBottom:5 }}>{label}</p>
            <code style={{ fontSize:11, fontFamily:'JetBrains Mono,monospace', color:'#3b82f6', userSelect:'all' as const }}>{cmd}</code>
          </div>
        ))}
      </Card>

      <Card title="About">
        {[
          ['Project',   'Adaptive GPU Resource Allocation'],
          ['Algorithm', 'Algorithm 1 — priority-weighted demand-proportional'],
          ['Agents',    'coord · nlp · vision · reasoning'],
          ['Platform',  'DGX H200 · 8× GPU · vLLM'],
          ['Backend',   'FastAPI + WebSocket'],
          ['Frontend',  'Next.js 14 · Tailwind · Recharts · Zustand'],
        ].map(([k,v],i,arr)=>(
          <div key={k} style={{ display:'flex', justifyContent:'space-between', padding:'6px 0', borderBottom: i<arr.length-1?'1px solid var(--border)':'none', fontSize:12, fontFamily:'JetBrains Mono,monospace' }}>
            <span style={{ color:'rgba(255,255,255,0.3)' }}>{k}</span>
            <span style={{ color:'rgba(255,255,255,0.6)' }}>{v}</span>
          </div>
        ))}
      </Card>
    </div>
  )
}
