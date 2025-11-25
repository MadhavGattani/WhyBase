// client/src/app/settings/integrations/page.tsx
"use client";

import React from "react";
import { useAuth } from "../../../hooks/useAuth";
import GitHubIntegration from "../../../components/integrations/GitHubIntegration";

export default function IntegrationsPage() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <main className="mx-auto max-w-4xl mt-8 px-4">
        <div className="flex items-center justify-center h-64">
          <div className="w-8 h-8 border-2 border-white/20 border-t-white/60 rounded-full animate-spin" />
        </div>
      </main>
    );
  }

  if (!isAuthenticated) {
    return (
      <main className="mx-auto max-w-4xl mt-8 px-4">
        <div className="p-8 bg-white/5 rounded-xl border border-white/10 text-center">
          <h2 className="text-xl font-semibold text-white mb-2">Sign in Required</h2>
          <p className="text-white/60">Please sign in to manage your integrations.</p>
        </div>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-4xl mt-8 px-4 pb-12">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Integrations</h1>
        <p className="text-white/60 mt-1">Connect external services to enhance your workflow</p>
      </div>

      <GitHubIntegration />

      {/* Placeholder for future integrations */}
      <div className="mt-6 p-6 bg-white/5 rounded-xl border border-white/10 border-dashed">
        <div className="text-center">
          <div className="w-12 h-12 mx-auto rounded-xl bg-white/10 flex items-center justify-center mb-3">
            <svg className="w-6 h-6 text-white/40" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
          </div>
          <h3 className="text-white/60 font-medium">More integrations coming soon</h3>
          <p className="text-sm text-white/40 mt-1">GitLab, Notion, Slack, and more</p>
        </div>
      </div>
    </main>
  );
}