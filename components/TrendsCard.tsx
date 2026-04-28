import { router } from 'expo-router';
import { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Dimensions,
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { BarChart, LineChart } from 'react-native-gifted-charts';

import { onboardingColors as c } from '@/components/OnboardingPage';
import { ApiError } from '@/lib/api';
import { getTrends, type TrendsRange, type TrendsResponse } from '@/lib/trends';

const RANGES: TrendsRange[] = ['7d', '30d', '90d'];

const COLOR_MOOD = c.brandOrange;
const COLOR_ENERGY = c.brandPurpleBright;
const COLOR_SCREEN = c.textPrimary;
const COLOR_AXIS = c.border;
const COLOR_AXIS_TEXT = c.textMuted;

// Card padding (14) + outer page padding (20) on both sides.
const CHART_HORIZONTAL_INSET = 2 * (14 + 20);

type Props = {
  refreshKey: number;
};

export function TrendsCard({ refreshKey }: Props) {
  const [range, setRange] = useState<TrendsRange>('7d');
  const [data, setData] = useState<TrendsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    getTrends(range)
      .then((d) => {
        if (!cancelled) setData(d);
      })
      .catch((e) => {
        if (cancelled) return;
        setError(e instanceof ApiError ? e.message : 'Failed to load trends');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [range, refreshKey]);

  return (
    <View style={styles.card}>
      <View style={styles.header}>
        <Text style={styles.title}>Trends</Text>
        <RangeToggle value={range} onChange={setRange} />
      </View>
      <Body data={data} loading={loading} error={error} range={range} />
    </View>
  );
}

function Body({
  data,
  loading,
  error,
  range,
}: {
  data: TrendsResponse | null;
  loading: boolean;
  error: string | null;
  range: TrendsRange;
}) {
  if (loading && !data) {
    return (
      <View style={styles.placeholder}>
        <ActivityIndicator color={c.textPrimary} />
      </View>
    );
  }
  if (error) {
    return (
      <View style={styles.placeholder}>
        <Text style={styles.errorText}>{error}</Text>
      </View>
    );
  }
  if (!data) return null;

  const allNull =
    data.mood.every((v) => v === null) &&
    data.energy.every((v) => v === null) &&
    data.screen_time_minutes.every((v) => v === null);

  if (allNull) {
    return (
      <View style={styles.empty}>
        <Text style={styles.emptyTitle}>No trend data yet</Text>
        <Text style={styles.emptyBody}>
          Log a check-in to start seeing your mood, energy, and screen-time
          trends.
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

  return <Charts data={data} range={range} />;
}

function Charts({ data, range }: { data: TrendsResponse; range: TrendsRange }) {
  const labels = sparseLabels(data.dates);
  const chartWidth = Dimensions.get('window').width - CHART_HORIZONTAL_INSET;
  // Two extra spacing slots account for initialSpacing + endSpacing.
  const spacing = Math.max(2, chartWidth / (data.dates.length + 1));

  const mood = carryForward(data.mood);
  const energy = carryForward(data.energy);
  const moodData = mood.values.map((v, i) => ({
    value: v,
    hideDataPoint: mood.hidden[i],
  }));
  const energyData = energy.values.map((v, i) => ({
    value: v,
    hideDataPoint: energy.hidden[i],
  }));

  const screenMax = Math.max(
    ...data.screen_time_minutes.map((v) => v ?? 0),
    60,
  );
  const screenStep = niceStep(screenMax);
  const screenAxisMax = Math.ceil(screenMax / screenStep) * screenStep;
  const barData = data.screen_time_minutes.map((v, i) => ({
    value: v ?? 0,
    label: labels[i],
    labelTextStyle: styles.axisLabel,
    frontColor: v === null ? 'transparent' : COLOR_SCREEN,
  }));

  return (
    <View style={styles.charts}>
      <SubHeader title="Mood & Energy" legend={MOOD_ENERGY_LEGEND} />
      <LineChart
        data={moodData}
        data2={energyData}
        color1={COLOR_MOOD}
        color2={COLOR_ENERGY}
        thickness={2}
        hideDataPoints
        maxValue={4}
        noOfSections={4}
        stepValue={1}
        yAxisOffset={0}
        yAxisColor={COLOR_AXIS}
        xAxisColor={COLOR_AXIS}
        rulesColor={COLOR_AXIS}
        rulesType="solid"
        yAxisTextStyle={styles.axisLabel}
        xAxisLabelTextStyle={styles.axisLabel}
        xAxisLabelTexts={labels}
        spacing={spacing}
        initialSpacing={spacing / 2}
        endSpacing={spacing / 2}
        height={120}
        disableScroll
        adjustToWidth
      />

      <SubHeader title="Screen time" legend={SCREEN_LEGEND} />
      <BarChart
        data={barData}
        barWidth={Math.max(2, spacing * 0.6)}
        spacing={spacing * 0.4}
        frontColor={COLOR_SCREEN}
        maxValue={screenAxisMax}
        stepValue={screenStep}
        noOfSections={Math.max(1, screenAxisMax / screenStep)}
        yAxisColor={COLOR_AXIS}
        xAxisColor={COLOR_AXIS}
        rulesColor={COLOR_AXIS}
        rulesType="solid"
        yAxisTextStyle={styles.axisLabel}
        xAxisLabelTextStyle={styles.axisLabel}
        formatYLabel={(v: string) => formatMinutesShort(Number(v))}
        height={100}
        disableScroll
      />

      <Text style={styles.rangeFooter}>{rangeFooterLabel(range, data)}</Text>
    </View>
  );
}

function RangeToggle({
  value,
  onChange,
}: {
  value: TrendsRange;
  onChange: (r: TrendsRange) => void;
}) {
  return (
    <View style={styles.toggleRow}>
      {RANGES.map((r) => {
        const selected = r === value;
        return (
          <Pressable
            key={r}
            onPress={() => onChange(r)}
            style={[styles.togglePill, selected && styles.togglePillSelected]}
          >
            <Text
              style={[
                styles.toggleText,
                selected && styles.toggleTextSelected,
              ]}
            >
              {r}
            </Text>
          </Pressable>
        );
      })}
    </View>
  );
}

function SubHeader({
  title,
  legend,
}: {
  title: string;
  legend: { color: string; label: string }[];
}) {
  return (
    <View style={styles.subHeader}>
      <Text style={styles.subHeaderTitle}>{title}</Text>
      <View style={styles.legendRow}>
        {legend.map((l) => (
          <View key={l.label} style={styles.legendItem}>
            <View style={[styles.legendDot, { backgroundColor: l.color }]} />
            <Text style={styles.legendText}>{l.label}</Text>
          </View>
        ))}
      </View>
    </View>
  );
}

const MOOD_ENERGY_LEGEND = [
  { color: COLOR_MOOD, label: 'Mood' },
  { color: COLOR_ENERGY, label: 'Energy' },
];
const SCREEN_LEGEND = [{ color: COLOR_SCREEN, label: 'Minutes' }];

// --- helpers ---------------------------------------------------------------

// gifted-charts has no native null support; carry the previous value forward
// so the line stays continuous, but flag the day so its data point is hidden.
function carryForward(values: (number | null)[]): {
  values: number[];
  hidden: boolean[];
} {
  const firstNonNull = values.find((v) => v !== null) ?? 0;
  let last = firstNonNull;
  const out: number[] = [];
  const hidden: boolean[] = [];
  for (const v of values) {
    if (v === null) {
      out.push(last);
      hidden.push(true);
    } else {
      last = v;
      out.push(v);
      hidden.push(false);
    }
  }
  return { values: out, hidden };
}

function sparseLabels(dates: string[]): string[] {
  const labels = new Array(dates.length).fill('');
  if (dates.length === 0) return labels;
  const indices =
    dates.length === 1
      ? [0]
      : [0, Math.floor(dates.length / 2), dates.length - 1];
  for (const i of indices) labels[i] = formatShortDate(dates[i]);
  return labels;
}

function formatShortDate(iso: string): string {
  const [y, m, d] = iso.split('-').map(Number);
  return new Date(y, m - 1, d).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
  });
}

// Pick a clean step so screen-time y-axis labels round to whole hours / halves.
function niceStep(maxMinutes: number): number {
  if (maxMinutes <= 60) return 15;
  if (maxMinutes <= 180) return 30;
  if (maxMinutes <= 360) return 60;
  if (maxMinutes <= 720) return 120;
  return 240;
}

function formatMinutesShort(total: number): string {
  if (total < 60) return `${total}m`;
  const h = total / 60;
  return Number.isInteger(h) ? `${h}h` : `${h.toFixed(1)}h`;
}

function rangeFooterLabel(range: TrendsRange, data: TrendsResponse): string {
  const start = formatShortDate(data.start_date);
  const end = formatShortDate(data.end_date);
  return `${range.toUpperCase()} · ${start} – ${end}`;
}

// --- styles ----------------------------------------------------------------

const styles = StyleSheet.create({
  card: {
    backgroundColor: c.surface,
    borderRadius: 10,
    padding: 14,
    gap: 12,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  title: {
    color: c.textPrimary,
    fontSize: 16,
    fontWeight: '600',
  },
  toggleRow: {
    flexDirection: 'row',
    gap: 6,
  },
  togglePill: {
    paddingVertical: 4,
    paddingHorizontal: 10,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: c.border,
  },
  togglePillSelected: {
    backgroundColor: c.brandPurple,
    borderColor: c.brandPurple,
  },
  toggleText: {
    color: c.textSecondary,
    fontSize: 12,
    fontWeight: '600',
  },
  toggleTextSelected: {
    color: c.textPrimary,
  },
  charts: {
    gap: 14,
  },
  subHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  subHeaderTitle: {
    color: c.textMuted,
    fontSize: 13,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  legendRow: {
    flexDirection: 'row',
    gap: 10,
  },
  legendItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  legendDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  legendText: {
    color: c.textMuted,
    fontSize: 11,
  },
  axisLabel: {
    color: COLOR_AXIS_TEXT,
    fontSize: 10,
  },
  rangeFooter: {
    color: c.textMuted,
    fontSize: 11,
    textAlign: 'center',
    marginTop: 2,
  },
  placeholder: {
    height: 220,
    alignItems: 'center',
    justifyContent: 'center',
  },
  errorText: {
    color: c.brandOrange,
    fontSize: 13,
    textAlign: 'center',
  },
  empty: {
    paddingVertical: 8,
    gap: 8,
  },
  emptyTitle: {
    color: c.textPrimary,
    fontSize: 15,
    fontWeight: '600',
  },
  emptyBody: {
    color: c.textSecondary,
    fontSize: 13,
  },
  emptyButton: {
    backgroundColor: c.brandPurple,
    borderRadius: 10,
    paddingVertical: 10,
    alignItems: 'center',
    marginTop: 4,
  },
  emptyButtonText: {
    color: c.textPrimary,
    fontSize: 14,
    fontWeight: '600',
  },
});
