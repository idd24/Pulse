import { router } from 'expo-router';

import { apiFetch, deleteToken } from '@/lib/api';

export type AuthUser = {
  id: string;
  email: string;
  created_at: string;
};

export type AuthResponse = {
  access_token: string;
  token_type: string;
  user: AuthUser;
};

export function registerUser(email: string, password: string) {
  return apiFetch<AuthResponse>('/api/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
}

export function loginUser(email: string, password: string) {
  return apiFetch<AuthResponse>('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
}

export function getMe() {
  return apiFetch<AuthUser>('/api/auth/me');
}

export async function logout() {
  await deleteToken();
  router.replace('/login');
}
