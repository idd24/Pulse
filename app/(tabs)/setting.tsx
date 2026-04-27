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
        <ActivityIndicator color="#fff" />
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
    backgroundColor: '#25292e',
    padding: 20,
    gap: 20,
  },
  loading: {
    flex: 1,
    backgroundColor: '#25292e',
    alignItems: 'center',
    justifyContent: 'center',
  },
  title: {
    color: '#fff',
    fontSize: 24,
    fontWeight: '600',
  },
  card: {
    backgroundColor: '#1f2328',
    borderRadius: 10,
    padding: 16,
    gap: 6,
  },
  label: {
    color: '#9ca3af',
    fontSize: 12,
  },
  email: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  logoutButton: {
    backgroundColor: '#1f2328',
    borderRadius: 10,
    paddingVertical: 14,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#f87171',
  },
  logoutText: {
    color: '#f87171',
    fontSize: 16,
    fontWeight: '600',
  },
  error: {
    color: '#f87171',
    fontSize: 14,
  },
  devButton: {
    paddingVertical: 12,
    alignItems: 'center',
  },
  devText: {
    color: '#9ca3af',
    fontSize: 13,
  },
});
