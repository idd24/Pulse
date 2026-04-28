import { router } from 'expo-router';
import { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { onboardingColors as c } from '@/components/OnboardingPage';
import { ApiError, deleteToken } from '@/lib/api';
import { getMe, logout, type AuthUser } from '@/lib/auth';
import { clearOnboarded } from '@/lib/onboarding';

export default function SettingScreen() {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getMe()
      .then(setUser)
      .catch((e) => {
        // 401 is already handled by apiFetch (redirect in flight).
        if (e instanceof ApiError && e.status === 401) return;
        setError(e instanceof Error ? e.message : 'Failed to load profile');
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <SafeAreaView edges={['top']} style={styles.loading}>
        <ActivityIndicator color={c.textPrimary} />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView edges={['top']} style={styles.container}>
      <Text style={styles.title}>Setting</Text>

      <View style={styles.card}>
        <Text style={styles.label}>Signed in as</Text>
        <Text style={styles.email}>{user?.email ?? '—'}</Text>
      </View>

      {error ? <Text style={styles.error}>{error}</Text> : null}

      <Pressable style={styles.logoutButton} onPress={logout}>
        <Text style={styles.logoutText}>Log out</Text>
      </Pressable>

      {__DEV__ && (
        <Pressable
          style={styles.devButton}
          onPress={async () => {
            await Promise.all([clearOnboarded(), deleteToken()]);
            router.replace('/intro');
          }}
        >
          <Text style={styles.devText}>Reset onboarding (dev)</Text>
        </Pressable>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: c.bg,
    padding: 20,
    gap: 20,
  },
  loading: {
    flex: 1,
    backgroundColor: c.bg,
    alignItems: 'center',
    justifyContent: 'center',
  },
  title: {
    color: c.textPrimary,
    fontSize: 24,
    fontWeight: '600',
  },
  card: {
    backgroundColor: c.surface,
    borderRadius: 10,
    padding: 16,
    gap: 6,
  },
  label: {
    color: c.textMuted,
    fontSize: 12,
  },
  email: {
    color: c.textPrimary,
    fontSize: 16,
    fontWeight: '600',
  },
  logoutButton: {
    backgroundColor: c.surface,
    borderRadius: 10,
    paddingVertical: 14,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: c.brandOrange,
  },
  logoutText: {
    color: c.brandOrange,
    fontSize: 16,
    fontWeight: '600',
  },
  error: {
    color: c.brandOrange,
    fontSize: 14,
  },
  devButton: {
    paddingVertical: 12,
    alignItems: 'center',
  },
  devText: {
    color: c.textMuted,
    fontSize: 13,
  },
});
