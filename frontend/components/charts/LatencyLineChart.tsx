'use client'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import { AGENT_COLORS, AGENTS } from '@/lib/constants'

interface MetricRow {
  elapsed_s: number
  agent: string
  avg_latency_ms: number
}

interface Props { rows: MetricRow[] }

export function LatencyLineChart({ rows }: Props) {
  // Pivot: [{elapsed_s, coord, nlp, vision, reasoning}]
  const byTime: Record<number, Record<string, number>> = {}
  for (const row of rows) {
    if (!byTime[row.elapsed_s]) byTime[row.elapsed_s] = { elapsed_s: row.elapsed_s }
    byTime[row.elapsed_s][row.agent] = Math.round(row.avg_latency_ms)
  }
  const data = Object.values(byTime).sort((a, b) => a.elapsed_s - b.elapsed_s)

  if (!data.length) return (
    <div className="h-[200px] flex items-center justify-center text-white/20 text-xs font-mono">No timeline data</div>
  )

  return (
    <ResponsiveContainer width="100%" height={200}>
      <LineChart data={data}>
        <XAxis dataKey="elapsed_s" tick={{ fill: '#8892a4', fontSize: 10, fontFamily: 'JetBrains Mono' }} axisLine={false} tickLine={false} tickFormatter={v => `${v}s`} />
        <YAxis tick={{ fill: '#8892a4', fontSize: 10, fontFamily: 'JetBrains Mono' }} axisLine={false} tickLine={false} tickFormatter={v => `${v}ms`} width={50} />
        <Tooltip
          contentStyle={{ background: '#1a1f2e', border: '1px solid rgba(255,255,255,0.12)', borderRadius: 8, fontFamily: 'JetBrains Mono', fontSize: 11 }}
          formatter={(v: number, name: string) => [`${v}ms`, name]}
        />
        {AGENTS.map(a => (
          <Line key={a} type="monotone" dataKey={a} stroke={AGENT_COLORS[a]} strokeWidth={2} dot={false} connectNulls />
        ))}
      </LineChart>
    </ResponsiveContainer>
  )
}
