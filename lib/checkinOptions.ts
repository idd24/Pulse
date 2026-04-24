// Keep these ids in sync with the Literal unions in backend/schemas.py.

export const ACTIVITIES = [
  { id: 'exercise', label: 'Exercise' },
  { id: 'work', label: 'Work' },
  { id: 'social', label: 'Social' },
  { id: 'outdoors', label: 'Outdoors' },
  { id: 'reading', label: 'Reading' },
  { id: 'gaming', label: 'Gaming' },
  { id: 'meditation', label: 'Meditation' },
  { id: 'chores', label: 'Chores' },
] as const;

export type ActivityId = (typeof ACTIVITIES)[number]['id'];

export const MOOD_EMOJI = ['😣', '😕', '😐', '🙂', '😄'] as const;

// Red (0) → green (4). Indexed by score; UI renders i+1 as the label.
export const ENERGY_COLORS = [
  '#ef4444',
  '#f59e0b',
  '#eab308',
  '#84cc16',
  '#22c55e',
] as const;

export const ENERGY_LABELS = ['Drained', 'Energized'] as const;
