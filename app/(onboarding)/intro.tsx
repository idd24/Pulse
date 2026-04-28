import { useRouter } from 'expo-router';
import { ArrowRight, CheckCircle2, Sparkles } from 'lucide-react-native';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { OnboardingPage, onboardingColors as c } from '@/components/OnboardingPage';

export default function IntroScreen() {
  const router = useRouter();

  return (
    <OnboardingPage
      step={1}
      footer={
        <Pressable style={styles.primary} onPress={() => router.push('/welcome')}>
          <Text style={styles.primaryText}>Next</Text>
          <ArrowRight color={c.textPrimary} size={20} />
        </Pressable>
      }
    >
      <View style={styles.iconWrap}>
        <CheckCircle2 color={c.textPrimary} size={56} strokeWidth={1.75} />
      </View>

      <Text style={styles.title}>Check in once a day</Text>
      <Text style={styles.lead}>
        Log your mood, energy, and screen time in under a minute. That&apos;s it
        — Pulse handles the rest.
      </Text>

      <View style={styles.callout}>
        <Sparkles color={c.textPrimary} size={22} strokeWidth={2} />
        <Text style={styles.calloutText}>
          Personal insights unlock after{' '}
          <Text style={styles.calloutEmphasis}>14 days</Text> of check-ins. Keep
          going — patterns get sharper the longer you log.
        </Text>
      </View>
    </OnboardingPage>
  );
}

const styles = StyleSheet.create({
  iconWrap: {
    alignSelf: 'center',
    width: 96,
    height: 96,
    borderRadius: 28,
    backgroundColor: c.brandPurpleSoft,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 28,
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
    marginBottom: 32,
  },
  callout: {
    flexDirection: 'row',
    gap: 12,
    backgroundColor: c.brandPurpleSoft,
    borderRadius: 16,
    padding: 16,
    alignItems: 'flex-start',
  },
  calloutText: {
    flex: 1,
    color: c.textPrimary,
    fontSize: 14,
    lineHeight: 20,
  },
  calloutEmphasis: {
    fontWeight: '700',
  },
  primary: {
    backgroundColor: c.brandPurple,
    borderRadius: 14,
    paddingVertical: 16,
    flexDirection: 'row',
    gap: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
  primaryText: {
    color: c.textPrimary,
    fontSize: 16,
    fontWeight: '600',
  },
});
