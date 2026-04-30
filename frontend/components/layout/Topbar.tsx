'use client'
import { useEffect, useState } from 'react'
import { usePathname } from 'next/navigation'
import { useExperimentStore } from '@/store/useExperimentStore'

const PAGE_TITLES: Record<string, string> = {
  '/':         'System Overview',
  '/runs':     'Experiment Runner',
  '/monitor':  'Live Monitor',
  '/results':  'Results Dashboard',
  '/history':  'Run History',
  '/settings': 'Settings',
}

const STATUS_STYLES: Record<string, React.CSSProperties> = {
  idle:      { background:'rgba(255,255,255,0.06)', color:'rgba(255,255,255,0.3)', border:'1px solid rgba(255,255,255,0.08)' },
  running:   { background:'rgba(245,158,11,0.12)',  color:'#f59e0b', border:'1px solid rgba(245,158,11,0.3)' },
  completed: { background:'rgba(16,185,129,0.12)',  color:'#10b981', border:'1px solid rgba(16,185,129,0.3)' },
  failed:    { background:'rgba(239,68,68,0.12)',   color:'#ef4444', border:'1px solid rgba(239,68,68,0.3)' },
  stopped:   { background:'rgba(255,255,255,0.06)', color:'rgba(255,255,255,0.3)', border:'1px solid rgba(255,255,255,0.08)' },
}

export function Topbar() {
  const path   = usePathname()
  const status = useExperimentStore(s => s.status)
  const [time, setTime] = useState('')

  useEffect(() => {
    const tick = () => setTime(new Date().toLocaleTimeString())
    tick()
    const id = setInterval(tick, 1000)
    return () => clearInterval(id)
  }, [])

  const badge = STATUS_STYLES[status.status] ?? STATUS_STYLES.idle

  return (
    <header className="topbar-wrap">
      <span style={{ flex:1, fontSize:14, fontWeight:600, color:'rgba(255,255,255,0.88)' }}>
        {PAGE_TITLES[path] ?? 'Dashboard'}
      </span>

      <span style={{ ...badge, padding:'3px 10px', borderRadius:20, fontSize:11, fontFamily:'JetBrains Mono,monospace', fontWeight:600 }}>
        {status.status === 'running' ? '● ' : ''}{status.status.toUpperCase()}
      </span>

      <span style={{ background:'rgba(16,185,129,0.08)', color:'#10b981', border:'1px solid rgba(16,185,129,0.2)', padding:'3px 10px', borderRadius:20, fontSize:10, fontFamily:'JetBrains Mono,monospace' }}>
        DGX H200 · 8× GPU
      </span>

      <span style={{ fontSize:11, fontFamily:'JetBrains Mono,monospace', color:'rgba(255,255,255,0.25)' }}>
        {time}
      </span>
    </header>
  )
}
