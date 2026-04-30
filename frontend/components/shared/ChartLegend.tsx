interface Item { label: string; color: string }

export function ChartLegend({ items }: { items: Item[] }) {
  return (
    <div style={{ display:'flex', flexWrap:'wrap', gap:12 }}>
      {items.map(({ label, color }) => (
        <div key={label} style={{ display:'flex', alignItems:'center', gap:5 }}>
          <span style={{ width:9, height:9, borderRadius:2, background:color, display:'inline-block', flexShrink:0 }}/>
          <span style={{ fontSize:11, fontFamily:'JetBrains Mono,monospace', color:'rgba(255,255,255,0.35)' }}>{label}</span>
        </div>
      ))}
    </div>
  )
}
