'use client'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { AGENTS, AGENT_COLORS } from '@/lib/constants'

interface Props { summary: Record<string, any>; policy: string }

export function GpuShareChart({ summary, policy }: Props) {
  const data = AGENTS.map(agent => ({
    agent: agent.toUpperCase(),
    share: parseFloat(((summary[policy]?.[agent]?.avg_gpu_share ?? 0) * 100).toFixed(1)),
    color: AGENT_COLORS[agent],
  }))

  return (
    <ResponsiveContainer width="100%" height={180}>
      <BarChart data={data} barCategoryGap="35%">
        <XAxis dataKey="agent" tick={{ fill: '#8892a4', fontSize: 10, fontFamily: 'JetBrains Mono' }} axisLine={false} tickLine={false} />
        <YAxis domain={[0, 65]} tick={{ fill: '#8892a4', fontSize: 10, fontFamily: 'JetBrains Mono' }} axisLine={false} tickLine={false} tickFormatter={v => `${v}%`} width={36} />
        <Tooltip
          contentStyle={{ background: '#1a1f2e', border: '1px solid rgba(255,255,255,0.12)', borderRadius: 8, fontFamily: 'JetBrains Mono', fontSize: 11 }}
          formatter={(v: number) => [`${v}%`, 'GPU Share']}
        />
        <Bar dataKey="share" radius={[4, 4, 0, 0]}>
          {data.map(entry => (
            <Cell key={entry.agent} fill={entry.color} fillOpacity={0.85} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
