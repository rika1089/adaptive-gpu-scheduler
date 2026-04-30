export const AGENTS = ['coord', 'nlp', 'vision', 'reasoning'] as const;
export const POLICIES = ['adaptive', 'static', 'round_robin'] as const;

export const POLICY_COLORS: Record<string, string> = {
  adaptive:    '#3b82f6',
  static:      '#10b981',
  round_robin: '#f59e0b',
};

export const AGENT_COLORS: Record<string, string> = {
  coord:     '#3b82f6',
  nlp:       '#10b981',
  vision:    '#8b5cf6',
  reasoning: '#f59e0b',
};

export const WORKLOADS = [
  { value: 'paper_default',  label: 'paper_default — 80/40/45/25 req/s (Paper Table 1)' },
  { value: 'low_load',       label: 'low_load — 10/10/10/10 req/s' },
  { value: 'burst_nlp',      label: 'burst_nlp — 20/100/10/15 req/s' },
  { value: 'high_reasoning', label: 'high_reasoning — 30/30/20/80 req/s' },
  { value: 'uniform',        label: 'uniform — 40/40/40/40 req/s' },
];
