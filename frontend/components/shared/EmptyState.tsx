export function EmptyState({ message }: { message: string }) {
  return (
    <div style={{ display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center', padding:'48px 0', gap:12 }}>
      <svg width="40" height="40" viewBox="0 0 40 40" fill="none" style={{ color:'rgba(255,255,255,0.1)' }}>
        <circle cx="20" cy="20" r="18" stroke="currentColor" strokeWidth="1.5" strokeDasharray="4 3"/>
        <path d="M14 20h12M20 14v12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" opacity="0.4"/>
      </svg>
      <p style={{ fontSize:12, fontFamily:'JetBrains Mono,monospace', color:'rgba(255,255,255,0.2)' }}>{message}</p>
    </div>
  )
}
