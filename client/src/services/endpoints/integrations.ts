// client/src/services/endpoints/integrations.ts

import { apiRequest, apiFetch, ApiOptions } from "../api";

export interface Integration {
  id: number;
  provider: string;
  provider_username: string;
  is_active: boolean;
  scopes: string[];
  created_at: string;
  last_sync_at: string | null;
}

export interface Repository {
  id: number;
  github_id: number;
  name: string;
  full_name: string;
  description: string | null;
  url: string;
  is_private: boolean;
  language: string | null;
  stars_count: number;
  forks_count: number;
  open_issues_count: number;
  is_synced: boolean;
  updated_at: string;
}

export interface Issue {
  id: number;
  github_id: number;
  number: number;
  title: string;
  body: string | null;
  state: "open" | "closed";
  url: string;
  labels: { name: string; color: string }[];
  assignees: { login: string; avatar_url: string }[];
  author_login: string | null;
  comments_count: number;
  github_created_at: string;
  github_updated_at: string;
}

export async function getIntegrations(options: ApiOptions = {}): Promise<{ integrations: Integration[] }> {
  return apiRequest("/api/integrations", options);
}

export async function connectGitHub(options: ApiOptions = {}): Promise<{ oauth_url: string }> {
  return apiRequest("/api/integrations/github/connect", options);
}

export async function disconnectGitHub(options: ApiOptions = {}): Promise<{ message: string }> {
  return apiRequest("/api/integrations/github/disconnect", {
    method: "POST",
    ...options,
  });
}

export async function getRepositories(options: ApiOptions = {}): Promise<{ repositories: Repository[] }> {
  return apiRequest("/api/integrations/github/repositories", options);
}

export async function syncGitHub(options: ApiOptions = {}): Promise<{ message: string; synced_repos: number; synced_issues: number }> {
  return apiRequest("/api/integrations/github/sync", {
    method: "POST",
    ...options,
  });
}

export async function getRepositoryIssues(
  repoId: number,
  state: "all" | "open" | "closed" = "all",
  options: ApiOptions = {}
): Promise<{ issues: Issue[] }> {
  return apiRequest(`/api/integrations/github/repositories/${repoId}/issues?state=${state}`, options);
}

export async function toggleRepositorySync(
  repoId: number,
  options: ApiOptions = {}
): Promise<{ repository: Repository }> {
  return apiRequest(`/api/integrations/github/repositories/${repoId}/toggle-sync`, {
    method: "POST",
    ...options,
  });
}