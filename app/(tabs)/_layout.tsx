import { Ionicons } from '@expo/vector-icons';
import { Redirect, Tabs } from 'expo-router';
import { useEffect, useState } from 'react';
import { StyleSheet } from 'react-native';

import { getToken } from '@/lib/api';
import { getMe } from '@/lib/auth';

type AuthStatus = 'loading' | 'authed' | 'anon';

export default function TabLayout() {
  const [status, setStatus] = useState<AuthStatus>('loading');

  useEffect(() => {
    getMe()
      .then(() => setStatus('authed'))
      .catch(async () => {
        // /me failed — if we still have a token it's probably a network
        // blip (offline launch), so render the tabs and let feature screens
        // surface their own errors. If no token, we're anon and need login.
        // A 401 with a token will have already cleared it inside apiFetch.
        const t = await getToken();
        setStatus(t ? 'authed' : 'anon');
      });
  }, []);

  if (status === 'loading') return null;
  if (status === 'anon') return <Redirect href="/login" />;

  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarStyle: {
          backgroundColor: '#1f2328',
          borderTopColor: '#2d333b',
          borderTopWidth: StyleSheet.hairlineWidth,
        },
        tabBarActiveTintColor: '#fff',
        tabBarInactiveTintColor: '#9ca3af',
        tabBarLabelStyle: {
          fontSize: 11,
          fontWeight: '500',
        },
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: 'Home',
          tabBarIcon: ({ color, focused, size }) => (
            <Ionicons
              name={focused ? 'home' : 'home-outline'}
              color={color}
              size={size}
            />
          ),
        }}
      />
      <Tabs.Screen
        name="checkin"
        options={{
          title: 'Check-in',
          tabBarIcon: ({ color, focused, size }) => (
            <Ionicons
              name={focused ? 'checkmark-circle' : 'checkmark-circle-outline'}
              color={color}
              size={size}
            />
          ),
        }}
      />
      <Tabs.Screen
        name="insights"
        options={{
          title: 'Insights',
          tabBarIcon: ({ color, focused, size }) => (
            <Ionicons
              name={focused ? 'stats-chart' : 'stats-chart-outline'}
              color={color}
              size={size}
            />
          ),
        }}
      />
      <Tabs.Screen
        name="setting"
        options={{
          title: 'Setting',
          tabBarIcon: ({ color, focused, size }) => (
            <Ionicons
              name={focused ? 'settings' : 'settings-outline'}
              color={color}
              size={size}
            />
          ),
        }}
      />
    </Tabs>
  );
}
