import { StyleSheet, Text, View } from 'react-native';

import { confidenceFromP, type InsightResponse } from '@/lib/insights';

type Props = { insight: InsightResponse };

const BADGE_STYLES: Record<
  'moderate' | 'strong' | 'very strong',
  { bg: string; fg: string }
> = {
  moderate:      { bg: '#2d333b',                 fg: '#9ca3af' },
  strong:        { bg: 'rgba(251, 191, 36, 0.15)', fg: '#fbbf24' },
  'very strong': { bg: 'rgba(74, 222, 128, 0.15)', fg: '#4ade80' },
};

export function InsightCard({ insight }: Props) {
  const conf = confidenceFromP(insight.p_value);
  const palette = BADGE_STYLES[conf.label];

  return (
    <View style={styles.card}>
      <View style={styles.header}>
        <Text style={styles.title} numberOfLines={2}>
          {insight.title}
        </Text>
        <View style={[styles.badge, { backgroundColor: palette.bg }]}>
          <Text style={[styles.badgeText, { color: palette.fg }]}>
            {conf.stars} {conf.label}
          </Text>
        </View>
      </View>
      {insight.category ? (
        <View style={styles.categoryPill}>
          <Text style={styles.categoryText}>{insight.category}</Text>
        </View>
      ) : null}
      <Text style={styles.body}>{insight.body}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#1f2328',
    borderRadius: 10,
    padding: 14,
    gap: 8,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
  },
  title: {
    flex: 1,
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
    lineHeight: 22,
  },
  badge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 999,
  },
  badgeText: {
    fontSize: 11,
    fontWeight: '600',
  },
  categoryPill: {
    alignSelf: 'flex-start',
    backgroundColor: '#2d333b',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 999,
  },
  categoryText: {
    color: '#9ca3af',
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 0.3,
    textTransform: 'uppercase',
  },
  body: {
    color: '#9ca3af',
    fontSize: 14,
    lineHeight: 20,
  },
});
