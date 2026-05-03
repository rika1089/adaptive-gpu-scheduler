'use client'
import { ScatterChart, Scatter, XAxis, YAxis, ZAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { POLICY_COLORS } from '@/lib/constants'

interface Props { summary: Record<string, any> }

const formatLatency = (ms: number) => {
  if (ms >= 1000) return `${(ms / 1000).toFixed(1)}s`
  return `${ms.toFixed(0)}ms`
}

export function CostPerformanceChart({ summary }: Props) {
  const data = Object.entries(summary).map(([pol, data]) => {
    const agents = { ...data }
    delete agents._fairness
    
    const latValues = Object.values(agents).map((a: any) => a.avg_latency_ms).filter(v => v > 0)
    const thrValues = Object.values(agents).map((a: any) => a.avg_throughput).filter(v => v > 0)
    
    const avgLat = latValues.length ? latValues.reduce((a, b) => a + b, 0) / latValues.length : 0
    const totalThr = thrValues.reduce((a, b) => a + b, 0)
    
    return {
      name: pol,
      latency: avgLat,
      throughput: totalThr,
      cost: 0.02 // Placeholder for "Cost" logic if needed, paper shows $0.020
    }
  }).filter(d => d.latency > 0)

  return (
    <ResponsiveContainer width="100%" height={250}>
      <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
        <XAxis 
          type="number" 
          dataKey="latency" 
          name="Avg Latency" 
          unit="" 
          tickFormatter={formatLatency}
          tick={{ fill: '#8892a4', fontSize: 10, fontFamily: 'JetBrains Mono' }}
          axisLine={false}
          tickLine={false}
          label={{ value: 'Average Latency', position: 'bottom', fill: '#8892a4', fontSize: 10, fontFamily: 'JetBrains Mono', offset: 0 }}
        />
        <YAxis 
          type="number" 
          dataKey="throughput" 
          name="Total Throughput" 
          unit=" r/s" 
          tick={{ fill: '#8892a4', fontSize: 10, fontFamily: 'JetBrains Mono' }}
          axisLine={false}
          tickLine={false}
          label={{ value: 'Total Throughput', angle: -90, position: 'left', fill: '#8892a4', fontSize: 10, fontFamily: 'JetBrains Mono' }}
        />
        <ZAxis type="number" range={[100, 100]} />
        <Tooltip 
          cursor={{ strokeDasharray: '3 3' }}
          contentStyle={{ background: '#1a1f2e', border: '1px solid rgba(255,255,255,0.12)', borderRadius: 8, fontFamily: 'JetBrains Mono', fontSize: 11 }}
          formatter={(v: any, name: string) => {
            if (name === 'Avg Latency') return [formatLatency(v), name]
            if (name === 'Total Throughput') return [`${v.toFixed(1)} req/s`, name]
            return [v, name]
          }}
        />
        <Scatter name="Policies" data={data}>
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={POLICY_COLORS[entry.name]} />
          ))}
        </Scatter>
      </ScatterChart>
    </ResponsiveContainer>
  )
}
