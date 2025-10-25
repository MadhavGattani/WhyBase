// client/src/lib/api.ts
export async function apiFetch(url: string, init: RequestInit = {}, token?: string | null) {
  const headers = new Headers(init.headers ?? {});
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const opts = { ...init, headers };
  return fetch(url, opts);
}
