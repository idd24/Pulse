import { apiFetch } from '@/lib/api';
import type { ActivityId, CategoryId } from '@/lib/checkinOptions';

export type CheckinPayload = {
  mood: number;
  energy: number;
  screen_time_minutes: number;
  top_category: CategoryId | null;
  activities: ActivityId[];
};

export type CheckinResponse = {
  id: string;
  date: string;
  mood: number;
  energy: number;
  screen_time_minutes: number;
  top_category: CategoryId | null;
  activities: ActivityId[];
  updated_at: string;
};

// Use the device's local calendar day so an entry made at 11pm
// doesn't roll onto the next UTC day in Postgres.
function todayHeader() {
  const d = new Date();
  const iso = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
  return { 'X-Client-Date': iso };
}

export function getTodayCheckin() {
  return apiFetch<CheckinResponse | null>('/api/checkins/today', {
    method: 'GET',
    headers: todayHeader(),
  });
}

export function saveCheckin(payload: CheckinPayload) {
  return apiFetch<CheckinResponse>('/api/checkins', {
    method: 'POST',
    headers: todayHeader(),
    body: JSON.stringify(payload),
  });
}
