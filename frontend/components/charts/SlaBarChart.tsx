'use client'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts'
import { AGENTS, POLICY_COLORS } from '@/lib/constants'

interface Props { summary: Record<string, any> }

export function SlaBarChart({ summary }: Props) {
  const data = AGENTS.map(agent => {
    const row: Record<string, any> = { agent: agent.toUpperCase() }
    for (const pol of Object.keys(summary)) {
      row[pol] = parseFloat(((summary[pol]?.[agent]?.avg_sla_violation ?? 0) * 100).toFixed(1))
    }
    return row
  })

  return (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart data={data} barCategoryGap="25%" barGap={2}>
        <XAxis dataKey="agent" tick={{ fill: '#8892a4', fontSize: 10, fontFamily: 'JetBrains Mono' }} axisLine={false} tickLine={false} />
        <YAxis domain={[0, 100]} tick={{ fill: '#8892a4', fontSize: 10, fontFamily: 'JetBrains Mono' }} axisLine={false} tickLine={false} tickFormatter={v => `${v}%`} width={36} />
        <ReferenceLine y={90} stroke="rgba(239,68,68,0.3)" strokeDasharray="4 3" />
        <Tooltip
          contentStyle={{ background: '#1a1f2e', border: '1px solid rgba(255,255,255,0.12)', borderRadius: 8, fontFamily: 'JetBrains Mono', fontSize: 11 }}
          formatter={(v: number, name: string) => [`${v}%`, name]}
        />
        {Object.keys(summary).map(pol => (
          <Bar key={pol} dataKey={pol} fill={POLICY_COLORS[pol]} radius={[3, 3, 0, 0]} />
        ))}
      </BarChart>
    </ResponsiveContainer>
  )
}
