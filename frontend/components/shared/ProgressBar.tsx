interface ProgressBarProps { value: number; color?: string; shimmer?: boolean; height?: number }

export function ProgressBar({ value, color = '#3b82f6', shimmer, height = 4 }: ProgressBarProps) {
  const pct = Math.min(100, Math.max(0, value))
  return (
    <div className="progress-track" style={{ height }}>
      <div
        className={shimmer ? 'progress-fill progress-shimmer' : 'progress-fill'}
        style={{ width:`${pct}%`, background: shimmer ? undefined : color, height:'100%' }}
      />
    </div>
  )
}
