import { apiFetch } from '@/lib/api';
import { todayHeader } from '@/lib/checkins';

export type DashboardWeekMetrics = {
  start_date: string;
  end_date: string;
  avg_mood: number | null;
  avg_energy: number | null;
  checkin_count: number;
  total_screen_time_minutes: number;
};

export type DashboardSummaryResponse = {
  current: DashboardWeekMetrics;
  previous: DashboardWeekMetrics;
};

export function getDashboardSummary() {
  return apiFetch<DashboardSummaryResponse>('/api/dashboard/summary', {
    method: 'GET',
    headers: todayHeader(),
  });
}
