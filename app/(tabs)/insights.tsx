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

import { InsightCard } from '@/components/InsightCard';
import { onboardingColors as c } from '@/components/OnboardingPage';
import { ApiError } from '@/lib/api';
import { getInsights, type InsightResponse } from '@/lib/insights';

export default function InsightsScreen() {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<InsightResponse[] | null>(null);

  function load() {
    setError(null);
    getInsights()
      .then((rows) => setData(rows))
      .catch((e) =>
        setError(e instanceof ApiError ? e.message : 'Failed to load insights'),
      )
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

  return (
    <SafeAreaView edges={['top']} style={styles.container}>
      <ScrollView
        contentContainerStyle={styles.content}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={() => {
              setRefreshing(true);
              load();
            }}
            tintColor={c.textPrimary}
          />
        }
      >
        <Text style={styles.title}>Insights</Text>
        {data.length === 0 ? (
          <EmptyState />
        ) : (
          data.map((insight) => (
            <InsightCard key={insight.id} insight={insight} />
          ))
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

function EmptyState() {
  return (
    <View style={styles.emptyCard}>
      <Text style={styles.emptyTitle}>No insights yet</Text>
      <Text style={styles.emptyBody}>
        Patterns appear once you have at least 14 days of check-ins. Keep
        logging — your trends will surface here.
      </Text>
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
    gap: 12,
  },
  loading: {
    flex: 1,
    backgroundColor: c.bg,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 20,
    gap: 12,
  },
  title: {
    color: c.textPrimary,
    fontSize: 24,
    fontWeight: '600',
    marginBottom: 4,
  },
  emptyCard: {
    backgroundColor: c.surface,
    borderRadius: 10,
    padding: 18,
    gap: 8,
  },
  emptyTitle: {
    color: c.textPrimary,
    fontSize: 16,
    fontWeight: '600',
  },
  emptyBody: {
    color: c.textSecondary,
    fontSize: 14,
    lineHeight: 20,
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
