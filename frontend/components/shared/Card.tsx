interface CardProps {
  title?: string
  action?: React.ReactNode
  children: React.ReactNode
  style?: React.CSSProperties
}

export function Card({ title, action, children, style }: CardProps) {
  return (
    <div className="glass" style={{ padding:16, ...style }}>
      {(title || action) && (
        <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:14 }}>
          {title && (
            <span style={{ fontSize:10, fontFamily:'JetBrains Mono,monospace', fontWeight:600, color:'rgba(255,255,255,0.28)', textTransform:'uppercase', letterSpacing:'0.08em' }}>
              {title}
            </span>
          )}
          {action && <div style={{ display:'flex', alignItems:'center', gap:8 }}>{action}</div>}
        </div>
      )}
      {children}
    </div>
  )
}
