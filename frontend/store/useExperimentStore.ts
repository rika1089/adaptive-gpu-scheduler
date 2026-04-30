import { create } from 'zustand';

export interface ExperimentConfig {
  policies: string[];
  workload: string;
  duration_seconds: number;
  repeats: number;
  random_seed: number;
  run_name: string;
}

export interface RunStatus {
  run_id: string;
  status: 'idle' | 'running' | 'completed' | 'failed' | 'stopped';
  current_policy: string | null;
  current_repeat: number;
  total_repeats: number;
  elapsed_seconds: number;
  estimated_remaining: number;
  progress_pct: number;
  started_at: string | null;
  message: string;
}

interface ExperimentStore {
  config: ExperimentConfig;
  status: RunStatus;
  logs: string[];
  summary: Record<string, any> | null;
  setConfig: (c: Partial<ExperimentConfig>) => void;
  setStatus: (s: Partial<RunStatus>) => void;
  addLog: (line: string) => void;
  clearLogs: () => void;
  setSummary: (s: Record<string, any>) => void;
}

const defaultStatus: RunStatus = {
  run_id: '', status: 'idle', current_policy: null,
  current_repeat: 0, total_repeats: 0, elapsed_seconds: 0,
  estimated_remaining: 0, progress_pct: 0, started_at: null, message: '',
};

export const useExperimentStore = create<ExperimentStore>((set) => ({
  config: {
    policies: ['adaptive', 'static', 'round_robin'],
    workload: 'paper_default',
    duration_seconds: 60,
    repeats: 1,
    random_seed: 42,
    run_name: '',
  },
  status: defaultStatus,
  logs: [],
  summary: null,
  setConfig: (c) => set((s) => ({ config: { ...s.config, ...c } })),
  setStatus: (st) => set((s) => ({ status: { ...s.status, ...st } })),
  addLog: (line) => set((s) => ({ logs: [...s.logs.slice(-500), line] })),
  clearLogs: () => set({ logs: [] }),
  setSummary: (sm) => set({ summary: sm }),
}));
