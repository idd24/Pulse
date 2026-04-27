import { useRouter } from 'expo-router';
import * as SplashScreen from 'expo-splash-screen';
import { ReactNode, useEffect, useRef, useState } from 'react';
import {
  Animated,
  Image,
  StyleSheet,
  View,
} from 'react-native';

import { getHasOnboarded } from '@/lib/onboarding';

// Hold the native splash until the JS overlay is on screen so the brand
// moment is continuous from icon tap → first interactive frame.
SplashScreen.preventAutoHideAsync().catch(() => {});

const SPLASH_BG = '#FFF1D3';
const MIN_DISPLAY_MS = 1100;

export function BootGate({ children }: { children: ReactNode }) {
  const [hidden, setHidden] = useState(false);
  const fade = useRef(new Animated.Value(1)).current;
  const router = useRouter();

  useEffect(() => {
    let alive = true;

    // Hand the splash off to our overlay on the next frame.
    requestAnimationFrame(() => {
      SplashScreen.hideAsync().catch(() => {});
    });

    const minDelay = new Promise<void>((r) => setTimeout(r, MIN_DISPLAY_MS));

    Promise.all([getHasOnboarded(), minDelay]).then(([onboarded]) => {
      if (!alive) return;
      if (!onboarded) {
        // Navigate under the overlay so the user sees onboarding
        // appear as the logo fades out.
        router.replace('/intro');
      }
      Animated.timing(fade, {
        toValue: 0,
        duration: 280,
        useNativeDriver: true,
      }).start(() => {
        if (alive) setHidden(true);
      });
    });

    return () => {
      alive = false;
    };
  }, [fade, router]);

  return (
    <View style={styles.root}>
      {children}
      {!hidden && (
        <Animated.View
          pointerEvents="none"
          style={[styles.overlay, { opacity: fade }]}
        >
          <Image
            source={require('../assets/images/logo.png')}
            style={styles.logo}
            resizeMode="contain"
          />
        </Animated.View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: SPLASH_BG,
  },
  overlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: SPLASH_BG,
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 10,
  },
  logo: {
    width: 200,
    height: 200,
  },
});
