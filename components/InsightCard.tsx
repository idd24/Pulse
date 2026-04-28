import { StyleSheet, Text, View } from 'react-native';

import { onboardingColors as c } from '@/components/OnboardingPage';
import { confidenceFromP, type InsightResponse } from '@/lib/insights';

type Props = { insight: InsightResponse };

const BADGE_STYLES: Record<
  'moderate' | 'strong' | 'very strong',
  { bg: string; fg: string }
> = {
  moderate:      { bg: 'transparent',     fg: c.textMuted },
  strong:        { bg: c.brandOrangeSoft, fg: c.brandOrange },
  'very strong': { bg: c.brandPurpleSoft, fg: c.brandPurpleBright },
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
    backgroundColor: c.surface,
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
    color: c.textPrimary,
    fontSize: 16,
    fontWeight: '600',
    lineHeight: 22,
  },
  badge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: c.border,
  },
  badgeText: {
    fontSize: 11,
    fontWeight: '600',
  },
  categoryPill: {
    alignSelf: 'flex-start',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: c.border,
  },
  categoryText: {
    color: c.textMuted,
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 0.3,
    textTransform: 'uppercase',
  },
  body: {
    color: c.textSecondary,
    fontSize: 14,
    lineHeight: 20,
  },
});
