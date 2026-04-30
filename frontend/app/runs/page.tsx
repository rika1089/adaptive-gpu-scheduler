'use client'
import { Card } from '@/components/shared/Card'
import { ExperimentForm } from '@/components/controls/ExperimentForm'
import { Terminal } from '@/components/logs/Terminal'

const CMDS = [
  { cmd:'bash scripts/run_simulation.sh --quick', desc:'30s smoke test, 1 repeat' },
  { cmd:'bash scripts/run_simulation.sh',         desc:'300s full paper run'     },
  { cmd:'bash scripts/run_all_experiments.sh',    desc:'All experiments + ablation' },
  { cmd:'bash scripts/launch_all.sh',             desc:'Start 4 vLLM agents on DGX'  },
]

export default function RunsPage() {
  return (
    <div className="animate-fade-in" style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:16 }}>
      <Card title="Experiment Configuration">
        <ExperimentForm />
      </Card>

      <div style={{ display:'flex', flexDirection:'column', gap:16 }}>
        <Card title="Live Log Stream">
          <Terminal maxHeight={420} />
        </Card>

        <Card title="Quick Commands">
          <div style={{ display:'flex', flexDirection:'column', gap:8 }}>
            {CMDS.map(({ cmd, desc }) => (
              <div key={cmd} style={{ background:'var(--bg-3)', borderRadius:8, padding:'10px 12px', border:'1px solid var(--border)' }}>
                <code style={{ fontSize:11, fontFamily:'JetBrains Mono,monospace', color:'#3b82f6', display:'block', marginBottom:3 }}>{cmd}</code>
                <span style={{ fontSize:10, color:'rgba(255,255,255,0.28)' }}>{desc}</span>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  )
}
