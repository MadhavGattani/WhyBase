// client/src/services/api.ts

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:5000";

export interface ApiOptions extends RequestInit {
  token?: string | null;
  organizationId?: number | null;
}

export async function apiFetch(
  endpoint: string,
  options: ApiOptions = {}
): Promise<Response> {
  const { token, organizationId, headers = {}, ...fetchOptions } = options;

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

  return fetch(url, {
    ...fetchOptions,
    headers: apiHeaders,
  });
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