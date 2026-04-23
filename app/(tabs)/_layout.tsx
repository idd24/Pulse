import { Redirect, Tabs } from 'expo-router';
import { useEffect, useState } from 'react';

import { getToken } from '@/lib/api';

type AuthStatus = 'loading' | 'authed' | 'anon';

export default function TabLayout() {
  const [status, setStatus] = useState<AuthStatus>('loading');

  useEffect(() => {
    getToken().then((t) => setStatus(t ? 'authed' : 'anon'));
  }, []);

  if (status === 'loading') return null;
  if (status === 'anon') return <Redirect href="/login" />;

  return (
    <Tabs>
      <Tabs.Screen name="index" options={{ title: 'Home' }} />
      <Tabs.Screen name="checkin" options={{ title: 'Check-in' }} />
      <Tabs.Screen name="insights" options={{ title: 'Insights' }} />
      <Tabs.Screen name="setting" options={{ title: 'Setting' }} />
    </Tabs>
  );
}
