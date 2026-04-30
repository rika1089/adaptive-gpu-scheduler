'use client'
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface HistoryEntry {
  run_id: string
  run_name: string
  started_at: string
  duration_seconds: number
  policies: string[]
  workload: string
  repeats: number
  status: string
  has_results: boolean
}

interface HistoryStore {
  entries: HistoryEntry[]
  addEntry: (e: HistoryEntry) => void
  clearEntries: () => void
}

export const useRunHistory = create<HistoryStore>()(
  persist(
    (set) => ({
      entries: [],
      addEntry: (e) =>
        set((s) => ({
          entries: [e, ...s.entries.filter(x => x.run_id !== e.run_id)].slice(0, 50),
        })),
      clearEntries: () => set({ entries: [] }),
    }),
    { name: 'gpu_run_history' },
  ),
)
