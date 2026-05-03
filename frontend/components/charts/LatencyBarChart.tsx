'use client'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import { AGENTS, POLICY_COLORS, AGENT_DISPLAY_NAMES } from '@/lib/constants'

interface Props { summary: Record<string, any> }

const formatLatency = (v: number) => {
  if (v >= 1000) return `${(v / 1000).toFixed(1)}s`
  return `${v}ms`
}

export function LatencyBarChart({ summary }: Props) {
  const data = AGENTS.map(agent => {
    const row: Record<string, any> = { agent: AGENT_DISPLAY_NAMES[agent] || agent }
    for (const pol of Object.keys(summary)) {
      row[pol] = Math.round(summary[pol]?.[agent]?.avg_latency_ms ?? 0)
    }
    return row
  })

  const policies = Object.keys(summary)

  return (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart data={data} barCategoryGap="25%" barGap={2}>
        <XAxis 
          dataKey="agent" 
          tick={{ fill: '#8892a4', fontSize: 9, fontFamily: 'JetBrains Mono' }} 
          axisLine={false} 
          tickLine={false} 
        />
        <YAxis 
          tick={{ fill: '#8892a4', fontSize: 10, fontFamily: 'JetBrains Mono' }} 
          axisLine={false} 
          tickLine={false} 
          tickFormatter={formatLatency}
          width={50} 
        />
        <Tooltip
          contentStyle={{ background: '#1a1f2e', border: '1px solid rgba(255,255,255,0.12)', borderRadius: 8, fontFamily: 'JetBrains Mono', fontSize: 11 }}
          labelStyle={{ color: '#e8eaf0', marginBottom: 4 }}
          itemStyle={{ color: '#8892a4' }}
          formatter={(v: number, name: string) => [formatLatency(v), name]}
        />
        {policies.map(pol => (
          <Bar key={pol} dataKey={pol} fill={POLICY_COLORS[pol]} radius={[3, 3, 0, 0]} />
        ))}
      </BarChart>
    </ResponsiveContainer>
  )
}
