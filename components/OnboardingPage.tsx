import { ReactNode } from 'react';
import { StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

export const onboardingColors = {
  bg: '#0A0A0A',
  surface: '#111114',
  border: 'rgba(255, 255, 255, 0.08)',
  textPrimary: '#FFFFFF',
  textSecondary: 'rgba(255, 255, 255, 0.65)',
  textMuted: 'rgba(255, 255, 255, 0.4)',
  brandPurple: '#5A189A',
  brandPurpleSoft: 'rgba(90, 24, 154, 0.20)',
  brandPurpleBright: '#9D4EDD',
  brandOrange: '#FF7900',
  brandOrangeSoft: 'rgba(255, 121, 0, 0.12)',
  dotActive: '#FFFFFF',
  dotInactive: 'rgba(255, 255, 255, 0.18)',
};

type Props = {
  step: 1 | 2;
  totalSteps?: number;
  children: ReactNode;
  footer: ReactNode;
};

export function OnboardingPage({ step, totalSteps = 2, children, footer }: Props) {
  return (
    <SafeAreaView edges={['top', 'bottom']} style={styles.root}>
      <View style={styles.dots}>
        {Array.from({ length: totalSteps }).map((_, i) => (
          <View
            key={i}
            style={[styles.dot, i + 1 === step && styles.dotActive]}
          />
        ))}
      </View>
      <View style={styles.body}>{children}</View>
      <View style={styles.footer}>{footer}</View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: onboardingColors.bg,
    paddingHorizontal: 28,
  },
  dots: {
    flexDirection: 'row',
    gap: 8,
    justifyContent: 'center',
    paddingTop: 12,
    paddingBottom: 8,
  },
  dot: {
    width: 22,
    height: 4,
    borderRadius: 2,
    backgroundColor: onboardingColors.dotInactive,
  },
  dotActive: {
    backgroundColor: onboardingColors.dotActive,
  },
  body: {
    flex: 1,
    justifyContent: 'center',
  },
  footer: {
    paddingBottom: 8,
    gap: 12,
  },
});
