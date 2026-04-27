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
        <View style={[styles.iconBubble, { backgroundColor: '#FFE3C9' }]}>
          <TrendingUp color={c.purple} size={32} strokeWidth={1.75} />
        </View>
        <View style={[styles.iconBubble, { backgroundColor: '#F9D2DF' }]}>
          <BarChart3 color={c.pink} size={32} strokeWidth={1.75} />
        </View>
      </View>

      <Text style={styles.title}>See yourself clearly</Text>
      <Text style={styles.lead}>
        Pulse turns your everyday check-ins into trends you can use — what
        lifts your mood, what drains your energy, what your week really looks
        like.
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
    alignItems: 'center',
    justifyContent: 'center',
  },
  title: {
    color: c.purple,
    fontSize: 30,
    fontWeight: '700',
    textAlign: 'center',
    letterSpacing: -0.5,
  },
  lead: {
    color: c.purpleSoft,
    fontSize: 16,
    lineHeight: 23,
    textAlign: 'center',
    marginTop: 12,
  },
  primary: {
    backgroundColor: c.purple,
    borderRadius: 14,
    paddingVertical: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  primaryText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  secondary: {
    paddingVertical: 12,
    alignItems: 'center',
  },
  secondaryText: {
    color: c.purple,
    fontSize: 14,
    fontWeight: '500',
  },
});
