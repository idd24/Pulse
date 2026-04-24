import { Redirect, Tabs } from 'expo-router';
import { useEffect, useState } from 'react';

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
    <Tabs>
      <Tabs.Screen name="index" options={{ title: 'Home' }} />
      <Tabs.Screen name="checkin" options={{ title: 'Check-in' }} />
      <Tabs.Screen name="insights" options={{ title: 'Insights' }} />
      <Tabs.Screen name="setting" options={{ title: 'Setting' }} />
    </Tabs>
  );
}
