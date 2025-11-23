// client/src/services/endpoints/templates.ts

import { apiRequest, ApiOptions } from "../api";
import { Template } from "../../types";

export async function getTemplates(options: ApiOptions = {}): Promise<{ templates: Template[] }> {
  return apiRequest("/api/templates", options);
}

export async function createTemplate(
  data: { name: string; prompt: string; description?: string },
  options: ApiOptions = {}
): Promise<{ template: Template }> {
  return apiRequest("/api/templates", {
    method: "POST",
    body: JSON.stringify(data),
    ...options,
  });
}

export async function updateTemplate(
  id: number,
  data: { name: string; prompt: string; description?: string },
  options: ApiOptions = {}
): Promise<{ template: Template }> {
  return apiRequest(`/api/templates/${id}`, {
    method: "PUT",
    body: JSON.stringify(data),
    ...options,
  });
}

export async function deleteTemplate(id: number, options: ApiOptions = {}): Promise<{ message: string }> {
  return apiRequest(`/api/templates/${id}`, {
    method: "DELETE",
    ...options,
  });
}