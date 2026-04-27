import * as SecureStore from 'expo-secure-store';

const ONBOARDED_KEY = 'pulse.has_onboarded';

export async function getHasOnboarded(): Promise<boolean> {
  const v = await SecureStore.getItemAsync(ONBOARDED_KEY);
  return v === '1';
}

export function markOnboarded() {
  return SecureStore.setItemAsync(ONBOARDED_KEY, '1');
}

export function clearOnboarded() {
  return SecureStore.deleteItemAsync(ONBOARDED_KEY);
}
