import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';

import { onboardingColors } from '@/components/OnboardingPage';

export default function OnboardingLayout() {
  return (
    <>
      <StatusBar style="dark" />
      <Stack
        screenOptions={{
          headerShown: false,
          gestureEnabled: false,
          animation: 'slide_from_right',
          contentStyle: { backgroundColor: onboardingColors.bg },
        }}
      />
    </>
  );
}
