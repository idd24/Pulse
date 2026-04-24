import { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { ApiError } from '@/lib/api';
import { getMe, logout, type AuthUser } from '@/lib/auth';

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
      <View style={styles.container}>
        <ActivityIndicator color="#fff" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.card}>
        <Text style={styles.label}>Signed in as</Text>
        <Text style={styles.email}>{user?.email ?? '—'}</Text>
      </View>

      {error ? <Text style={styles.error}>{error}</Text> : null}

      <Pressable style={styles.logoutButton} onPress={logout}>
        <Text style={styles.logoutText}>Log out</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#25292e',
    padding: 20,
    gap: 20,
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
});
