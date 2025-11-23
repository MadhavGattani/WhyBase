// client/src/services/endpoints/uploads.ts

import { apiFetch, ApiOptions } from "../api";
import { Upload } from "../../types";

export async function uploadFile(file: File, options: ApiOptions = {}): Promise<{ upload: Upload }> {
  const { token, organizationId } = options;
  
  const formData = new FormData();
  formData.append("file", file);

  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (organizationId) headers["X-Organization-Id"] = String(organizationId);

  const response = await apiFetch("/api/upload", {
    method: "POST",
    body: formData,
    headers,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: "Upload failed" }));
    throw new Error(error.error || "Upload failed");
  }

  return response.json();
}

export async function getUploads(
  page: number = 1,
  perPage: number = 10,
  options: ApiOptions = {}
): Promise<{ uploads: Upload[]; meta: { page: number; pages: number; total: number } }> {
  const response = await apiFetch(`/api/uploads?page=${page}&per_page=${perPage}`, options);
  
  if (!response.ok) {
    throw new Error("Failed to fetch uploads");
  }

  return response.json();
}

export function getDownloadUrl(fileId: number): string {
  const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:5000";
  return `${API_URL}/api/download/${fileId}`;
}