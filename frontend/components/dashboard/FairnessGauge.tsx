'use client'
import { POLICY_COLORS } from '@/lib/constants'

interface Props { policy: string; value: number }

export function FairnessGauge({ policy, value }: Props) {
  const color = POLICY_COLORS[policy] ?? '#8892a4'
  // Arc: semicircle 0..π mapped to 0..value
  const R = 34
  const circumference = Math.PI * R
  const filled = value * circumference

  return (
    <div className="flex flex-col items-center gap-2">
      <svg width="84" height="52" viewBox="0 0 84 52" fill="none">
        {/* Track */}
        <path d="M8 46 A34 34 0 0 1 76 46" stroke="rgba(255,255,255,0.08)" strokeWidth="7" strokeLinecap="round" fill="none" />
        {/* Fill */}
        <path
          d="M8 46 A34 34 0 0 1 76 46"
          stroke={color}
          strokeWidth="7"
          strokeLinecap="round"
          fill="none"
          strokeDasharray={`${filled} ${circumference}`}
          opacity="0.9"
        />
        <text x="42" y="44" textAnchor="middle" fontSize="13" fontFamily="JetBrains Mono" fontWeight="600" fill={color}>
          {value.toFixed(3)}
        </text>
      </svg>
      <span className="text-[10px] font-mono text-white/30">{policy}</span>
    </div>
  )
}
