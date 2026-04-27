import { ReactNode } from 'react';
import { StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

export const onboardingColors = {
  bg: '#FFF1D3',
  peach: '#FFB090',
  pink: '#CA5995',
  purple: '#5D1C6A',
  purpleSoft: 'rgba(93, 28, 106, 0.65)',
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
    backgroundColor: 'rgba(93, 28, 106, 0.18)',
  },
  dotActive: {
    backgroundColor: onboardingColors.purple,
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
