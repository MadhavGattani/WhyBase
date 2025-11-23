// client/src/services/endpoints/queries.ts

import { apiRequest, ApiOptions } from "../api";
import { Query } from "../../types";

export async function queryAI(prompt: string, options: ApiOptions = {}): Promise<{ response: string }> {
  return apiRequest("/api/query", {
    method: "POST",
    body: JSON.stringify({ prompt }),
    ...options,
  });
}

export async function getQueries(options: ApiOptions = {}): Promise<{ queries: Query[] }> {
  return apiRequest("/api/queries", options);
}