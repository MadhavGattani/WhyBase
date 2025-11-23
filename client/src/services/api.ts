// client/src/services/api.ts

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:5000";
const DEFAULT_TIMEOUT = 30000; // 30 seconds

export interface ApiOptions extends RequestInit {
  token?: string | null;
  organizationId?: number | null;
  timeout?: number;
}

// ✅ Create abort controller with timeout
function createTimeoutController(timeout: number): AbortController {
  const controller = new AbortController();
  setTimeout(() => controller.abort(), timeout);
  return controller;
}

export async function apiFetch(
  endpoint: string,
  options: ApiOptions = {}
): Promise<Response> {
  const { token, organizationId, timeout = DEFAULT_TIMEOUT, headers = {}, signal, ...fetchOptions } = options;

  const apiHeaders: Record<string, string> = {
    "Content-Type": "application/json",
    ...headers as Record<string, string>,
  };

  if (token) {
    apiHeaders["Authorization"] = `Bearer ${token}`;
  }

  if (organizationId) {
    apiHeaders["X-Organization-Id"] = String(organizationId);
  }

  const url = `${API_URL}${endpoint}`;

  // ✅ Create timeout controller if no signal provided
  const timeoutController = !signal ? createTimeoutController(timeout) : null;
  const finalSignal = signal || timeoutController?.signal;

  try {
    const response = await fetch(url, {
      ...fetchOptions,
      headers: apiHeaders,
      signal: finalSignal,
    });

    return response;
  } catch (error: any) {
    if (error.name === 'AbortError') {
      throw new Error('Request timeout - please try again');
    }
    throw error;
  }
}

export async function apiRequest<T>(
  endpoint: string,
  options: ApiOptions = {}
): Promise<T> {
  const response = await apiFetch(endpoint, options);

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: "Request failed" }));
    throw new Error(error.error || `HTTP ${response.status}`);
  }

  return response.json();
}