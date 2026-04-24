import { apiFetch } from '@/lib/api';
import type { ActivityId } from '@/lib/checkinOptions';

export type CheckinPayload = {
  mood: number;
  energy: number;
  activities: ActivityId[];
};

export type CheckinResponse = {
  id: string;
  date: string;
  mood: number;
  energy: number;
  activities: ActivityId[];
  updated_at: string;
};

export type ScreentimePayload = {
  social: number;
  entertainment: number;
  productivity: number;
};

export type ScreentimeResponse = {
  id: string;
  date: string;
  social: number;
  entertainment: number;
  productivity: number;
  updated_at: string;
};

// Use the device's local calendar day so an entry made at 11pm
// doesn't roll onto the next UTC day in Postgres.
export function localDateIso() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

export function todayHeader() {
  return { 'X-Client-Date': localDateIso() };
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

export async function getTodayScreentime(): Promise<ScreentimeResponse | null> {
  const today = localDateIso();
  const rows = await apiFetch<ScreentimeResponse[]>(
    `/api/screentime?start_date=${today}&end_date=${today}`,
    { method: 'GET', headers: todayHeader() },
  );
  return rows[0] ?? null;
}

export function saveScreentime(payload: ScreentimePayload) {
  return apiFetch<ScreentimeResponse>('/api/screentime', {
    method: 'POST',
    headers: todayHeader(),
    body: JSON.stringify(payload),
  });
}
