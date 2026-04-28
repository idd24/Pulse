import { router } from 'expo-router';
import { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { InsightCard as InsightCardComponent } from '@/components/InsightCard';
import { onboardingColors as c } from '@/components/OnboardingPage';
import { TrendsCard } from '@/components/TrendsCard';
import { getMe, type AuthUser } from '@/lib/auth';
import { getTodayCheckin, type CheckinResponse } from '@/lib/checkins';
import {
  getDashboardSummary,
  type DashboardSummaryResponse,
} from '@/lib/dashboard';
import { getTopInsights, type InsightResponse } from '@/lib/insights';

type LoadedData = {
  me: AuthUser;
  summary: DashboardSummaryResponse;
  today: CheckinResponse | null;
  topInsight: InsightResponse | null;
};

type DeltaDirection = 'up' | 'down' | 'flat' | 'none';
type DeltaKind = 'score' | 'minutes';

function greetingFor(hour: number) {
  if (hour < 12) return 'Good morning';
  if (hour < 18) return 'Good afternoon';
  return 'Good evening';
}

function nameFromEmail(email: string) {
  return email.split('@')[0] ?? '';
}

function formatMinutesHM(total: number) {
  const h = Math.floor(total / 60);
  const m = total % 60;
  if (h === 0) return `${m}m`;
  if (m === 0) return `${h}h`;
  return `${h}h ${m}m`;
}

function formatAvg(v: number | null) {
  return v === null ? '—' : v.toFixed(1);
}

function formatDelta(
  curr: number | null,
  prev: number | null,
  kind: DeltaKind,
): { text: string; direction: DeltaDirection } {
  if (curr === null || prev === null) return { text: '—', direction: 'none' };
  const diff = curr - prev;
  if (diff === 0) return { text: '·  no change', direction: 'flat' };
  const arrow = diff > 0 ? '↑' : '↓';
  const abs = Math.abs(diff);
  const magnitude =
    kind === 'minutes' ? formatMinutesHM(Math.round(abs)) : abs.toFixed(1);
  return { text: `${arrow} ${magnitude}`, direction: diff > 0 ? 'up' : 'down' };
}

// Mood/energy going up is good; screen time going up is bad. Flip per metric.
function deltaColor(direction: DeltaDirection, goodDirection: 'up' | 'down') {
  if (direction === 'none' || direction === 'flat') return c.textMuted;
  return direction === goodDirection ? c.textPrimary : c.brandOrange;
}

export default function HomeScreen() {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<LoadedData | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  function load() {
    setError(null);
    Promise.all([
      getMe(),
      getDashboardSummary(),
      getTodayCheckin(),
      getTopInsights(1),
    ])
      .then(([me, summary, today, topInsights]) =>
        setData({ me, summary, today, topInsight: topInsights[0] ?? null }),
      )
      .catch((e) => setError(e instanceof Error ? e.message : 'Failed to load'))
      .finally(() => {
        setLoading(false);
        setRefreshing(false);
      });
  }

  useEffect(() => {
    load();
  }, []);

  if (loading) {
    return (
      <SafeAreaView edges={['top']} style={styles.loading}>
        <ActivityIndicator color={c.textPrimary} />
      </SafeAreaView>
    );
  }

  if (error || !data) {
    return (
      <SafeAreaView edges={['top']} style={styles.loading}>
        <Text style={styles.error}>{error ?? 'Failed to load'}</Text>
        <Pressable
          onPress={() => {
            setLoading(true);
            load();
          }}
          style={styles.retry}
        >
          <Text style={styles.retryText}>Tap to retry</Text>
        </Pressable>
      </SafeAreaView>
    );
  }

  const { me, summary, today } = data;
  const isEmpty =
    summary.current.checkin_count === 0 &&
    summary.current.total_screen_time_minutes === 0;

  return (
    <SafeAreaView edges={['top']} style={styles.container}>
      <ScrollView
        contentContainerStyle={styles.content}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={() => {
              setRefreshing(true);
              setRefreshKey((k) => k + 1);
              load();
            }}
            tintColor={c.textPrimary}
          />
        }
      >
        <GreetingBlock name={nameFromEmail(me.email)} />
        <CheckinStatusPill checkedIn={today !== null} />

        <Text style={styles.sectionLabel}>This week</Text>
        {isEmpty ? <EmptyCard /> : <MetricsRow summary={summary} />}

        <TrendsCard refreshKey={refreshKey} />

        <TopInsightSection insight={data.topInsight} />
      </ScrollView>
    </SafeAreaView>
  );
}

function GreetingBlock({ name }: { name: string }) {
  const greeting = greetingFor(new Date().getHours());
  return (
    <Text style={styles.greeting}>
      {greeting}
      {name ? `, ${name}` : ''}
    </Text>
  );
}

function CheckinStatusPill({ checkedIn }: { checkedIn: boolean }) {
  return (
    <Pressable
      onPress={() => router.push('/checkin')}
      style={styles.statusPill}
    >
      <Text style={styles.statusText}>
        {checkedIn ? (
          <>
            <Text style={styles.statusCheck}>✓</Text> You&apos;ve checked in today
          </>
        ) : (
          'Tap to check in today  →'
        )}
      </Text>
    </Pressable>
  );
}

function MetricsRow({ summary }: { summary: DashboardSummaryResponse }) {
  const { current, previous } = summary;
  const moodDelta = formatDelta(current.avg_mood, previous.avg_mood, 'score');
  const energyDelta = formatDelta(
    current.avg_energy,
    previous.avg_energy,
    'score',
  );
  const screenDelta = formatDelta(
    current.total_screen_time_minutes,
    previous.total_screen_time_minutes,
    'minutes',
  );

  return (
    <View style={styles.metricsRow}>
      <MetricCard
        label="Mood"
        value={formatAvg(current.avg_mood)}
        deltaText={moodDelta.text}
        deltaColor={deltaColor(moodDelta.direction, 'up')}
      />
      <MetricCard
        label="Energy"
        value={formatAvg(current.avg_energy)}
        deltaText={energyDelta.text}
        deltaColor={deltaColor(energyDelta.direction, 'up')}
      />
      <MetricCard
        label="Screen"
        value={formatMinutesHM(current.total_screen_time_minutes)}
        deltaText={screenDelta.text}
        deltaColor={deltaColor(screenDelta.direction, 'down')}
      />
    </View>
  );
}

function MetricCard({
  label,
  value,
  deltaText,
  deltaColor: color,
}: {
  label: string;
  value: string;
  deltaText: string;
  deltaColor: string;
}) {
  return (
    <View style={styles.metricCard}>
      <Text style={styles.metricLabel}>{label}</Text>
      <Text style={styles.metricValue}>{value}</Text>
      <Text style={[styles.metricDelta, { color }]}>{deltaText}</Text>
    </View>
  );
}

function EmptyCard() {
  return (
    <View style={styles.emptyCard}>
      <Text style={styles.emptyTitle}>No data yet</Text>
      <Text style={styles.emptyBody}>
        Start with your first check-in to see your week here.
      </Text>
      <Pressable
        style={styles.emptyButton}
        onPress={() => router.push('/checkin')}
      >
        <Text style={styles.emptyButtonText}>Check in now</Text>
      </Pressable>
    </View>
  );
}

function TopInsightSection({ insight }: { insight: InsightResponse | null }) {
  if (!insight) {
    return (
      <View style={styles.insightCard}>
        <Text style={styles.insightTitle}>Top insight</Text>
        <Text style={styles.insightBody}>
          Patterns appear once you have at least 14 days of check-ins. Keep
          logging — your trends will surface here.
        </Text>
      </View>
    );
  }

  return (
    <View style={styles.insightSection}>
      <InsightCardComponent insight={insight} />
      <Pressable
        onPress={() => router.push('/insights')}
        style={styles.seeAllRow}
      >
        <Text style={styles.seeAllText}>See all insights →</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: c.bg,
  },
  content: {
    padding: 20,
    paddingBottom: 48,
    gap: 16,
  },
  loading: {
    flex: 1,
    backgroundColor: c.bg,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 20,
    gap: 12,
  },
  greeting: {
    color: c.textPrimary,
    fontSize: 22,
    fontWeight: '600',
  },
  statusPill: {
    backgroundColor: c.surface,
    borderRadius: 10,
    paddingVertical: 14,
    paddingHorizontal: 16,
  },
  statusText: {
    color: c.textPrimary,
    fontSize: 15,
  },
  statusCheck: {
    color: c.brandPurpleBright,
    fontWeight: '700',
  },
  sectionLabel: {
    color: c.textMuted,
    fontSize: 13,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginTop: 4,
  },
  metricsRow: {
    flexDirection: 'row',
    gap: 10,
  },
  metricCard: {
    flex: 1,
    backgroundColor: c.surface,
    borderRadius: 10,
    padding: 14,
    gap: 4,
  },
  metricLabel: {
    color: c.textMuted,
    fontSize: 13,
  },
  metricValue: {
    color: c.textPrimary,
    fontSize: 22,
    fontWeight: '600',
  },
  metricDelta: {
    fontSize: 13,
    marginTop: 2,
  },
  emptyCard: {
    backgroundColor: c.surface,
    borderRadius: 10,
    padding: 18,
    gap: 10,
  },
  emptyTitle: {
    color: c.textPrimary,
    fontSize: 16,
    fontWeight: '600',
  },
  emptyBody: {
    color: c.textSecondary,
    fontSize: 14,
  },
  emptyButton: {
    backgroundColor: c.brandPurple,
    borderRadius: 10,
    paddingVertical: 12,
    alignItems: 'center',
    marginTop: 4,
  },
  emptyButtonText: {
    color: c.textPrimary,
    fontSize: 15,
    fontWeight: '600',
  },
  insightCard: {
    backgroundColor: c.surface,
    borderRadius: 10,
    padding: 14,
    gap: 6,
  },
  insightTitle: {
    color: c.textPrimary,
    fontSize: 16,
    fontWeight: '600',
  },
  insightBody: {
    color: c.textSecondary,
    fontSize: 14,
    lineHeight: 20,
  },
  insightSection: {
    backgroundColor: c.surface,
    borderRadius: 10,
    overflow: 'hidden',
  },
  seeAllRow: {
    paddingVertical: 12,
    paddingHorizontal: 14,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: c.border,
    alignItems: 'center',
  },
  seeAllText: {
    color: c.textSecondary,
    fontSize: 14,
    fontWeight: '500',
  },
  error: {
    color: c.brandOrange,
    fontSize: 14,
    textAlign: 'center',
  },
  retry: {
    paddingVertical: 8,
    paddingHorizontal: 14,
  },
  retryText: {
    color: c.textPrimary,
    fontSize: 14,
    textDecorationLine: 'underline',
  },
});
