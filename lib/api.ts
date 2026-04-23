import Constants from 'expo-constants';
import * as SecureStore from 'expo-secure-store';

const BACKEND_PORT = 8000;

// Dev networking: a physical iPhone can't reach the Mac's `localhost`, but it
// *can* reach whatever LAN IP Metro is already serving the JS bundle on. So we
// pull that host from expo-constants and swap Metro's port for the backend's.
// `EXPO_PUBLIC_API_URL` is an explicit override (e.g. an ngrok URL or prod).
function resolveApiBaseUrl(): string {
  const override = process.env.EXPO_PUBLIC_API_URL;
  if (override) return override;

  const hostUri = Constants.expoConfig?.hostUri;
  if (hostUri) {
    const host = hostUri.split(':')[0];
    return `http://${host}:${BACKEND_PORT}`;
  }

  return `http://localhost:${BACKEND_PORT}`;
}

export const API_BASE_URL = resolveApiBaseUrl();

const TOKEN_KEY = 'pulse.access_token';

export function saveToken(token: string) {
  return SecureStore.setItemAsync(TOKEN_KEY, token);
}

export function getToken() {
  return SecureStore.getItemAsync(TOKEN_KEY);
}

export function deleteToken() {
  return SecureStore.deleteItemAsync(TOKEN_KEY);
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export async function apiFetch<T = unknown>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const headers = new Headers(options.headers);

  const token = await getToken();
  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
  }
  if (options.body && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });
  } catch {
    throw new ApiError(0, 'Could not reach server');
  }

  const body = await res.json().catch(() => ({}));

  if (!res.ok) {
    // FastAPI returns `detail` as a string for HTTPException, or an array of
    // issues for Pydantic validation errors (422).
    let message = 'Something went wrong';
    if (typeof body?.detail === 'string') message = body.detail;
    else if (Array.isArray(body?.detail)) message = body.detail[0]?.msg ?? 'Invalid input';
    throw new ApiError(res.status, message);
  }

  return body as T;
}
