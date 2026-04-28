import { useRouter } from 'expo-router';
import { BarChart3, TrendingUp } from 'lucide-react-native';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { OnboardingPage, onboardingColors as c } from '@/components/OnboardingPage';
import { markOnboarded } from '@/lib/onboarding';

export default function WelcomeScreen() {
  const router = useRouter();

  async function go(target: '/register' | '/login') {
    await markOnboarded();
    router.replace(target);
  }

  return (
    <OnboardingPage
      step={2}
      footer={
        <>
          <Pressable style={styles.primary} onPress={() => go('/register')}>
            <Text style={styles.primaryText}>Get started</Text>
          </Pressable>
          <Pressable style={styles.secondary} onPress={() => go('/login')}>
            <Text style={styles.secondaryText}>Already have an account? Log in</Text>
          </Pressable>
        </>
      }
    >
      <View style={styles.iconRow}>
        <View style={styles.iconBubble}>
          <TrendingUp color={c.textPrimary} size={32} strokeWidth={1.75} />
        </View>
        <View style={styles.iconBubble}>
          <BarChart3 color={c.textPrimary} size={32} strokeWidth={1.75} />
        </View>
      </View>

      <Text style={styles.title}>See yourself clearly</Text>
      <Text style={styles.lead}>
        <Text style={styles.leadBrand}>Pulse</Text> turns your everyday
        check-ins into trends you can use — what lifts your mood, what drains
        your energy, what your week really looks like.
      </Text>
    </OnboardingPage>
  );
}

const styles = StyleSheet.create({
  iconRow: {
    flexDirection: 'row',
    gap: 16,
    justifyContent: 'center',
    marginBottom: 28,
  },
  iconBubble: {
    width: 80,
    height: 80,
    borderRadius: 24,
    backgroundColor: c.brandPurpleSoft,
    alignItems: 'center',
    justifyContent: 'center',
  },
  title: {
    color: c.textPrimary,
    fontSize: 30,
    fontWeight: '700',
    textAlign: 'center',
    letterSpacing: -0.5,
  },
  lead: {
    color: c.textSecondary,
    fontSize: 16,
    lineHeight: 23,
    textAlign: 'center',
    marginTop: 12,
  },
  leadBrand: {
    color: c.brandOrange,
    fontWeight: '600',
  },
  primary: {
    backgroundColor: c.brandPurple,
    borderRadius: 14,
    paddingVertical: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  primaryText: {
    color: c.textPrimary,
    fontSize: 16,
    fontWeight: '600',
  },
  secondary: {
    paddingVertical: 12,
    alignItems: 'center',
  },
  secondaryText: {
    color: c.brandOrange,
    fontSize: 14,
    fontWeight: '500',
  },
});
