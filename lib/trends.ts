import { apiFetch } from '@/lib/api';
import { todayHeader } from '@/lib/checkins';

export type TrendsRange = '7d' | '30d' | '90d';

export type TrendsResponse = {
  range: TrendsRange;
  start_date: string;
  end_date: string;
  dates: string[];
  mood: (number | null)[];
  energy: (number | null)[];
  screen_time_minutes: (number | null)[];
};

export function getTrends(range: TrendsRange) {
  return apiFetch<TrendsResponse>(`/api/dashboard/trends?range=${range}`, {
    method: 'GET',
    headers: todayHeader(),
  });
}
