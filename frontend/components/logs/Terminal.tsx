'use client'
import { useEffect, useRef } from 'react'
import { useExperimentStore } from '@/store/useExperimentStore'

function classify(line: string): string {
  if (line.startsWith('✅')||line.startsWith('▶')) return '#10b981'
  if (line.startsWith('❌')||line.startsWith('⛔')) return '#ef4444'
  if (line.startsWith('🚀')) return '#3b82f6'
  if (line.startsWith('[API]'))  return '#3b82f6'
  if (line.startsWith('[Warn]')) return '#f59e0b'
  if (line.startsWith('─')||line==='') return 'rgba(255,255,255,0.1)'
  if (line.startsWith('#'))  return 'rgba(255,255,255,0.18)'
  return 'rgba(255,255,255,0.5)'
}

export function Terminal({ maxHeight = 220 }: { maxHeight?: number }) {
  const logs   = useExperimentStore(s => s.logs)
  const bodyRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (bodyRef.current) bodyRef.current.scrollTop = bodyRef.current.scrollHeight
  }, [logs])

  return (
    <div style={{ borderRadius:12, overflow:'hidden', border:'1px solid var(--border)' }}>
      {/* Traffic lights */}
      <div style={{ display:'flex', alignItems:'center', gap:6, padding:'8px 12px', background:'var(--bg-2)', borderBottom:'1px solid var(--border)' }}>
        {['#ef4444','#f59e0b','#10b981'].map(c=>(
          <span key={c} style={{ width:9, height:9, borderRadius:'50%', background:c, display:'inline-block' }}/>
        ))}
        <span style={{ marginLeft:6, fontSize:10, fontFamily:'JetBrains Mono,monospace', color:'rgba(255,255,255,0.2)' }}>
          terminal · ws://localhost:8000/ws/logs
        </span>
      </div>
      {/* Body */}
      <div ref={bodyRef} className="terminal-body" style={{ maxHeight }}>
        {logs.length === 0 ? (
          <>
            <span style={{ color:'rgba(255,255,255,0.2)' }}># Adaptive GPU Scheduler — ready{'\n'}</span>
            <span style={{ color:'rgba(255,255,255,0.2)' }}># Configure experiment and press Run{'\n'}</span>
            <span style={{ color:'rgba(255,255,255,0.2)' }}># Logs stream here via WebSocket</span>
          </>
        ) : logs.map((line,i) => (
          <span key={i} style={{ color: classify(line), display:'block' }}>{line}</span>
        ))}
      </div>
    </div>
  )
}
