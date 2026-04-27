import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';

import { onboardingColors } from '@/components/OnboardingPage';

export default function AuthLayout() {
  return (
    <>
      <StatusBar style="light" />
      <Stack
        screenOptions={{
          headerShown: false,
          contentStyle: { backgroundColor: onboardingColors.bg },
        }}
      />
    </>
  );
}
