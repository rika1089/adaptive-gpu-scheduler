const COLORS: Record<string, { accent: string; bg: string; border: string }> = {
  blue:   { accent:'#3b82f6', bg:'rgba(59,130,246,0.07)',  border:'rgba(59,130,246,0.15)' },
  green:  { accent:'#10b981', bg:'rgba(16,185,129,0.07)',  border:'rgba(16,185,129,0.15)' },
  amber:  { accent:'#f59e0b', bg:'rgba(245,158,11,0.07)',  border:'rgba(245,158,11,0.15)' },
  purple: { accent:'#8b5cf6', bg:'rgba(139,92,246,0.07)',  border:'rgba(139,92,246,0.15)' },
  cyan:   { accent:'#06b6d4', bg:'rgba(6,182,212,0.07)',   border:'rgba(6,182,212,0.15)'  },
}

interface KpiCardProps { label: string; value: string; sub?: string; color?: keyof typeof COLORS }

export function KpiCard({ label, value, sub, color = 'blue' }: KpiCardProps) {
  const c = COLORS[color] ?? COLORS.blue
  return (
    <div className="kpi-card" style={{ background: c.bg, border:`1px solid ${c.border}` }}>
      <div className="kpi-accent" style={{ background: c.accent }} />
      <p style={{ fontSize:10, fontFamily:'JetBrains Mono,monospace', textTransform:'uppercase', letterSpacing:'0.08em', color:'rgba(255,255,255,0.28)', marginBottom:6 }}>{label}</p>
      <p style={{ fontSize:22, fontWeight:700, fontFamily:'JetBrains Mono,monospace', lineHeight:1, marginBottom:4, color: c.accent }}>{value}</p>
      {sub && <p style={{ fontSize:11, color:'rgba(255,255,255,0.3)' }}>{sub}</p>}
    </div>
  )
}
