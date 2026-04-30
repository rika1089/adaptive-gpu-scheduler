'use client'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { AGENT_COLORS } from '@/lib/constants'

interface AllocRow { elapsed_s: number; coord: number; nlp: number; vision: number; reasoning: number; policy: string }
interface Props { data: AllocRow[]; title?: string }

export function AllocationLineChart({ data, title }: Props) {
  if (!data.length) return <div className="h-[200px] flex items-center justify-center text-white/20 text-xs font-mono">No allocation data</div>
  const agents = ['coord', 'nlp', 'vision', 'reasoning'] as const

  return (
    <ResponsiveContainer width="100%" height={200}>
      <LineChart data={data}>
        <XAxis dataKey="elapsed_s" tick={{ fill: '#8892a4', fontSize: 10, fontFamily: 'JetBrains Mono' }} axisLine={false} tickLine={false} tickFormatter={v => `${v}s`} />
        <YAxis domain={[0, 0.7]} tick={{ fill: '#8892a4', fontSize: 10, fontFamily: 'JetBrains Mono' }} axisLine={false} tickLine={false} tickFormatter={v => `${(v * 100).toFixed(0)}%`} width={40} />
        <Tooltip
          contentStyle={{ background: '#1a1f2e', border: '1px solid rgba(255,255,255,0.12)', borderRadius: 8, fontFamily: 'JetBrains Mono', fontSize: 11 }}
          formatter={(v: number, name: string) => [`${(v * 100).toFixed(1)}%`, name]}
        />
        {agents.map(a => (
          <Line key={a} type="monotone" dataKey={a} stroke={AGENT_COLORS[a]} strokeWidth={2} dot={false} />
        ))}
      </LineChart>
    </ResponsiveContainer>
  )
}
