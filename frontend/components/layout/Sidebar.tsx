'use client'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { LayoutDashboard, Play, Activity, BarChart3, Clock, Settings, Cpu } from 'lucide-react'

const NAV = [
  { href: '/',         label: 'Overview',     icon: LayoutDashboard, section: 'Monitor'  },
  { href: '/runs',     label: 'Experiment',   icon: Play,            section: 'Monitor'  },
  { href: '/monitor',  label: 'Live Monitor', icon: Activity,        section: 'Monitor'  },
  { href: '/results',  label: 'Results',      icon: BarChart3,       section: 'Analysis' },
  { href: '/history',  label: 'History',      icon: Clock,           section: 'Analysis' },
  { href: '/settings', label: 'Settings',     icon: Settings,        section: 'Config'   },
]
const SECTIONS = ['Monitor', 'Analysis', 'Config']

export function Sidebar() {
  const path = usePathname()
  return (
    <aside className="sidebar-wrap">
      {/* Logo */}
      <div style={{ padding: '20px 16px 16px', borderBottom: '1px solid var(--border)' }}>
        <div style={{ display:'flex', alignItems:'center', gap:10 }}>
          <div style={{ width:28, height:28, borderRadius:6, background:'linear-gradient(135deg,#3b82f6,#8b5cf6)', display:'flex', alignItems:'center', justifyContent:'center', flexShrink:0 }}>
            <Cpu size={14} color="white" />
          </div>
          <div>
            <div style={{ fontSize:13, fontWeight:700, letterSpacing:'0.04em', color:'white' }}>GPU SCHED</div>
            <div style={{ fontSize:10, color:'rgba(255,255,255,0.25)', fontFamily:'JetBrains Mono,monospace', marginTop:2 }}>v1.0 · DGX H200</div>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav style={{ flex:1, padding:'12px 8px', display:'flex', flexDirection:'column', gap:2 }}>
        {SECTIONS.map(section => (
          <div key={section}>
            <p style={{ fontSize:10, fontFamily:'JetBrains Mono,monospace', color:'rgba(255,255,255,0.18)', textTransform:'uppercase', letterSpacing:'0.1em', padding:'12px 10px 4px' }}>{section}</p>
            {NAV.filter(n => n.section === section).map(({ href, label, icon: Icon }) => {
              const active = path === href
              return (
                <Link
                  key={href}
                  href={href}
                  style={{
                    display:'flex', alignItems:'center', gap:10,
                    padding:'9px 10px', borderRadius:8, fontSize:13,
                    textDecoration:'none', transition:'all 0.15s',
                    background: active ? 'rgba(59,130,246,0.1)' : 'transparent',
                    color: active ? '#3b82f6' : 'rgba(255,255,255,0.4)',
                    border: active ? '1px solid rgba(59,130,246,0.22)' : '1px solid transparent',
                  }}
                >
                  <Icon size={15} style={{ opacity: active ? 1 : 0.5 }} />
                  <span>{label}</span>
                </Link>
              )
            })}
          </div>
        ))}
      </nav>

      {/* Status footer */}
      <div style={{ padding:12, borderTop:'1px solid var(--border)', display:'flex', alignItems:'center', gap:8, fontSize:11, fontFamily:'JetBrains Mono,monospace', color:'rgba(255,255,255,0.25)' }}>
        <span className="animate-pulse2" style={{ width:6, height:6, borderRadius:'50%', background:'#10b981', display:'inline-block', flexShrink:0 }} />
        localhost:8000
      </div>
    </aside>
  )
}
