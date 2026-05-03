export const AGENTS = ['coord', 'nlp', 'vision', 'reasoning'] as const;

export const AGENT_DISPLAY_NAMES: Record<string, string> = {
  coord:     'Coordinator',
  nlp:       'Specialist (NLP)',
  vision:    'Specialist (Vision)',
  reasoning: 'Specialist (Reasoning)',
};
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
  { value: 'paper_default',  label: 'paper_default — 100s (Paper Table 1)' },
  { value: 'low_load',       label: 'low_load — 120s duration' },
  { value: 'burst_nlp',      label: 'burst_nlp — 180s duration' },
  { value: 'high_reasoning', label: 'high_reasoning — 180s duration' },
  { value: 'uniform',        label: 'uniform — 120s duration' },
];
