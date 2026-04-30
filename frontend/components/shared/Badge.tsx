type Variant = 'blue' | 'green' | 'amber' | 'red' | 'purple' | 'dim'

const V: Record<Variant, React.CSSProperties> = {
  blue:   { background:'rgba(59,130,246,0.12)',  color:'#3b82f6', border:'1px solid rgba(59,130,246,0.22)'  },
  green:  { background:'rgba(16,185,129,0.12)',  color:'#10b981', border:'1px solid rgba(16,185,129,0.22)'  },
  amber:  { background:'rgba(245,158,11,0.12)',  color:'#f59e0b', border:'1px solid rgba(245,158,11,0.22)'  },
  red:    { background:'rgba(239,68,68,0.12)',   color:'#ef4444', border:'1px solid rgba(239,68,68,0.22)'   },
  purple: { background:'rgba(139,92,246,0.12)',  color:'#8b5cf6', border:'1px solid rgba(139,92,246,0.22)'  },
  dim:    { background:'rgba(255,255,255,0.06)', color:'rgba(255,255,255,0.3)', border:'1px solid rgba(255,255,255,0.1)' },
}

export function Badge({ children, variant = 'blue', style }: {
  children: React.ReactNode; variant?: Variant; style?: React.CSSProperties
}) {
  return (
    <span style={{ ...V[variant], display:'inline-flex', alignItems:'center', padding:'2px 9px', borderRadius:20, fontSize:10, fontFamily:'JetBrains Mono,monospace', fontWeight:600, ...style }}>
      {children}
    </span>
  )
}
