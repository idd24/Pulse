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

// Indexed by score; UI renders i+1 as the label.
export const ENERGY_LEVELS = [0, 1, 2, 3, 4] as const;

export const ENERGY_LABELS = ['Drained', 'Energized'] as const;
