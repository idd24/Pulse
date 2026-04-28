import { useRouter } from 'expo-router';
import {
  AlertCircle,
  Eye,
  EyeOff,
  Lock,
  Mail,
  UserPlus,
} from 'lucide-react-native';
import { useState } from 'react';
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { onboardingColors as c } from '@/components/OnboardingPage';
import { saveToken } from '@/lib/api';
import { registerUser } from '@/lib/auth';

export default function RegisterScreen() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit() {
    setError(null);
    setLoading(true);
    try {
      const res = await registerUser(email.trim(), password);
      await saveToken(res.access_token);
      router.replace('/');
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Something went wrong');
    } finally {
      setLoading(false);
    }
  }

  const disabled = loading || !email || !password;

  return (
    <SafeAreaView edges={['top', 'bottom']} style={styles.root}>
      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        <View style={styles.body}>
          <View style={styles.hero}>
            <View style={styles.iconBubble}>
              <UserPlus color={c.textPrimary} size={32} strokeWidth={1.75} />
            </View>
            <Text style={styles.title}>Create your account</Text>
            <Text style={styles.subtitle}>Start logging in under a minute.</Text>
          </View>

          <View style={styles.form}>
            <View style={styles.field}>
              <Mail color={c.textPrimary} size={18} strokeWidth={2} />
              <TextInput
                style={styles.input}
                placeholder="Email"
                placeholderTextColor={c.textMuted}
                autoCapitalize="none"
                autoComplete="email"
                keyboardType="email-address"
                value={email}
                onChangeText={setEmail}
              />
            </View>

            <View>
              <View style={styles.field}>
                <Lock color={c.textPrimary} size={18} strokeWidth={2} />
                <TextInput
                  style={styles.input}
                  placeholder="Password"
                  placeholderTextColor={c.textMuted}
                  secureTextEntry={!showPassword}
                  autoCapitalize="none"
                  value={password}
                  onChangeText={setPassword}
                />
                <Pressable
                  onPress={() => setShowPassword((v) => !v)}
                  hitSlop={8}
                >
                  {showPassword ? (
                    <EyeOff color={c.textPrimary} size={18} strokeWidth={2} />
                  ) : (
                    <Eye color={c.textPrimary} size={18} strokeWidth={2} />
                  )}
                </Pressable>
              </View>
              <Text style={styles.helper}>At least 8 characters</Text>
            </View>

            {error ? (
              <View style={styles.errorCard}>
                <AlertCircle color={c.brandOrange} size={16} strokeWidth={2} />
                <Text style={styles.errorText}>{error}</Text>
              </View>
            ) : null}

            <Pressable
              style={[styles.primary, disabled && styles.primaryDisabled]}
              onPress={onSubmit}
              disabled={disabled}
            >
              {loading ? (
                <ActivityIndicator color={c.textPrimary} />
              ) : (
                <Text style={styles.primaryText}>Create account</Text>
              )}
            </Pressable>

            <Pressable
              style={styles.secondary}
              onPress={() => router.replace('/login')}
            >
              <Text style={styles.secondaryText}>
                Already have an account?{' '}
                <Text style={styles.secondaryEmphasis}>Log in</Text>
              </Text>
            </Pressable>
          </View>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: c.bg,
  },
  flex: {
    flex: 1,
    paddingHorizontal: 28,
  },
  body: {
    flex: 1,
    justifyContent: 'center',
    paddingBottom: 16,
  },
  hero: {
    alignItems: 'center',
    marginBottom: 32,
  },
  iconBubble: {
    width: 80,
    height: 80,
    borderRadius: 24,
    backgroundColor: c.brandPurpleSoft,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 20,
  },
  title: {
    color: c.textPrimary,
    fontSize: 30,
    fontWeight: '700',
    letterSpacing: -0.5,
    textAlign: 'center',
  },
  subtitle: {
    color: c.textSecondary,
    fontSize: 16,
    textAlign: 'center',
    marginTop: 8,
  },
  form: {
    gap: 12,
  },
  field: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    backgroundColor: c.surface,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: c.border,
    paddingHorizontal: 14,
    paddingVertical: Platform.OS === 'ios' ? 14 : 10,
  },
  input: {
    flex: 1,
    color: c.textPrimary,
    fontSize: 16,
    padding: 0,
  },
  helper: {
    color: c.textMuted,
    fontSize: 12,
    marginTop: 6,
    marginLeft: 4,
  },
  errorCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    backgroundColor: c.brandOrangeSoft,
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 12,
  },
  errorText: {
    flex: 1,
    color: c.textPrimary,
    fontSize: 14,
    lineHeight: 20,
  },
  primary: {
    backgroundColor: c.brandPurple,
    borderRadius: 14,
    paddingVertical: 16,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 8,
  },
  primaryDisabled: {
    opacity: 0.5,
  },
  primaryText: {
    color: c.textPrimary,
    fontSize: 16,
    fontWeight: '600',
  },
  secondary: {
    paddingVertical: 12,
    alignItems: 'center',
    marginTop: 4,
  },
  secondaryText: {
    color: c.textSecondary,
    fontSize: 14,
  },
  secondaryEmphasis: {
    color: c.brandOrange,
    fontWeight: '600',
  },
});
