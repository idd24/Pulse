import { apiFetch } from '@/lib/api';

export type InsightResponse = {
  id: string;
  template_key: string;
  variable_a: string;
  variable_b: string;
  direction: 'positive' | 'negative';
  title: string;
  body: string;
  r: number;
  p_value: number;
  n: number;
  created_at: string;
  updated_at: string;
};

export type ConfidenceLevel = 'moderate' | 'strong' | 'very strong';

export type Confidence = {
  stars: '★★' | '★★★' | '★★★★';
  label: ConfidenceLevel;
  longLabel: 'Moderate evidence' | 'Strong evidence' | 'Very strong evidence';
};

// Mirrors backend/insight_templates.py:confidence_from_p — keep in sync.
export function confidenceFromP(p: number): Confidence {
  if (p < 0.001)
    return { stars: '★★★★', label: 'very strong', longLabel: 'Very strong evidence' };
  if (p < 0.01)
    return { stars: '★★★', label: 'strong', longLabel: 'Strong evidence' };
  return { stars: '★★', label: 'moderate', longLabel: 'Moderate evidence' };
}

export function getInsights() {
  return apiFetch<InsightResponse[]>('/api/insights');
}
