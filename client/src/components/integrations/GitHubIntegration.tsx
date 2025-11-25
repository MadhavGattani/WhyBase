// client/src/components/integrations/GitHubIntegration.tsx
"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "../../hooks/useAuth";
import { useToast } from "../../hooks/useToast";
import * as integrationsApi from "../../services/endpoints/integrations";
import type { Integration, Repository } from "../../services/endpoints/integrations";

export default function GitHubIntegration() {
  const [integration, setIntegration] = useState<Integration | null>(null);
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [connecting, setConnecting] = useState(false);
  
  const { getToken } = useAuth();
  const toast = useToast();

  useEffect(() => {
    loadIntegration();
    
    // Check URL params for OAuth callback
    const params = new URLSearchParams(window.location.search);
    const success = params.get("success");
    const error = params.get("error");
    
    if (success === "github_connected") {
      toast.push("GitHub connected successfully!", "success");
      window.history.replaceState({}, "", window.location.pathname);
      loadIntegration();
    } else if (error) {
      toast.push(`Connection failed: ${error}`, "error");
      window.history.replaceState({}, "", window.location.pathname);
    }
  }, []);

  const loadIntegration = async () => {
    setLoading(true);
    try {
      const token = await getToken();
      const data = await integrationsApi.getIntegrations({ token });
      const github = data.integrations.find(i => i.provider === "github");
      setIntegration(github || null);
      
      if (github) {
        const repoData = await integrationsApi.getRepositories({ token });
        setRepositories(repoData.repositories);
      }
    } catch (error) {
      console.error("Failed to load integration:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleConnect = async () => {
    setConnecting(true);
    try {
      const token = await getToken();
      const data = await integrationsApi.connectGitHub({ token });
      window.location.href = data.oauth_url;
    } catch (error: any) {
      toast.push(error.message || "Failed to connect", "error");
      setConnecting(false);
    }
  };

  const handleDisconnect = async () => {
    if (!confirm("Are you sure you want to disconnect GitHub? This will remove all synced data.")) {
      return;
    }
    
    try {
      const token = await getToken();
      await integrationsApi.disconnectGitHub({ token });
      setIntegration(null);
      setRepositories([]);
      toast.push("GitHub disconnected", "success");
    } catch (error: any) {
      toast.push(error.message || "Failed to disconnect", "error");
    }
  };

  const handleSync = async () => {
    setSyncing(true);
    try {
      const token = await getToken();
      const result = await integrationsApi.syncGitHub({ token });
      toast.push(`Synced ${result.synced_repos} repos, ${result.synced_issues} issues`, "success");
      await loadIntegration();
    } catch (error: any) {
      toast.push(error.message || "Sync failed", "error");
    } finally {
      setSyncing(false);
    }
  };

  const handleToggleSync = async (repoId: number) => {
    try {
      const token = await getToken();
      const result = await integrationsApi.toggleRepositorySync(repoId, { token });
      setRepositories(repos => 
        repos.map(r => r.id === repoId ? result.repository : r)
      );
    } catch (error: any) {
      toast.push(error.message || "Failed to toggle sync", "error");
    }
  };

  if (loading) {
    return (
      <div className="p-6 bg-white/5 rounded-xl">
        <div className="flex items-center gap-3">
          <div className="w-6 h-6 border-2 border-white/20 border-t-white/60 rounded-full animate-spin" />
          <span className="text-white/60">Loading...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Connection Card */}
      <div className="p-6 bg-white/5 rounded-xl border border-white/10">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-[#24292e] flex items-center justify-center">
              <svg className="w-7 h-7 text-white" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
              </svg>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-white">GitHub</h3>
              {integration ? (
                <p className="text-sm text-white/60">
                  Connected as <span className="text-white/80 font-medium">@{integration.provider_username}</span>
                </p>
              ) : (
                <p className="text-sm text-white/60">Connect to sync repositories and issues</p>
              )}
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            {integration ? (
              <>
                <button
                  onClick={handleSync}
                  disabled={syncing}
                  className="px-4 py-2 bg-primary hover:bg-primary/90 text-white rounded-lg font-medium transition-colors disabled:opacity-50 flex items-center gap-2"
                >
                  {syncing ? (
                    <>
                      <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                      </svg>
                      Syncing...
                    </>
                  ) : (
                    <>
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                      Sync
                    </>
                  )}
                </button>
                <button
                  onClick={handleDisconnect}
                  className="px-4 py-2 bg-red-500/20 hover:bg-red-500/30 text-red-300 rounded-lg font-medium transition-colors"
                >
                  Disconnect
                </button>
              </>
            ) : (
              <button
                onClick={handleConnect}
                disabled={connecting}
                className="px-4 py-2 bg-[#24292e] hover:bg-[#2f363d] text-white rounded-lg font-medium transition-colors disabled:opacity-50 flex items-center gap-2"
              >
                {connecting ? (
                  <>
                    <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    Connecting...
                  </>
                ) : (
                  <>
                    <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                    </svg>
                    Connect GitHub
                  </>
                )}
              </button>
            )}
          </div>
        </div>
        
        {integration && (
          <div className="mt-4 pt-4 border-t border-white/10 flex items-center gap-4 text-sm text-white/60">
            <span>Last synced: {integration.last_sync_at ? new Date(integration.last_sync_at).toLocaleString() : "Never"}</span>
            <span>•</span>
            <span>Scopes: {integration.scopes.join(", ")}</span>
          </div>
        )}
      </div>

      {/* Repositories List */}
      {integration && repositories.length > 0 && (
        <div className="p-6 bg-white/5 rounded-xl border border-white/10">
          <h4 className="text-lg font-semibold text-white mb-4">Repositories ({repositories.length})</h4>
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {repositories.map(repo => (
              <RepositoryCard 
                key={repo.id} 
                repo={repo} 
                onToggleSync={() => handleToggleSync(repo.id)}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function RepositoryCard({ repo, onToggleSync }: { repo: Repository; onToggleSync: () => void }) {
  const [expanded, setExpanded] = useState(false);
  const [issues, setIssues] = useState<any[]>([]);
  const [loadingIssues, setLoadingIssues] = useState(false);
  const { getToken } = useAuth();

  const loadIssues = async () => {
    if (issues.length > 0) {
      setExpanded(!expanded);
      return;
    }
    
    setLoadingIssues(true);
    setExpanded(true);
    try {
      const token = await getToken();
      const data = await integrationsApi.getRepositoryIssues(repo.id, "all", { token });
      setIssues(data.issues);
    } catch (error) {
      console.error("Failed to load issues:", error);
    } finally {
      setLoadingIssues(false);
    }
  };

  return (
    <div className="p-4 bg-white/5 rounded-lg">
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <a 
              href={repo.url} 
              target="_blank" 
              rel="noopener noreferrer"
              className="font-medium text-white hover:text-primary transition-colors truncate"
            >
              {repo.full_name}
            </a>
            {repo.is_private && (
              <span className="px-2 py-0.5 bg-yellow-500/20 text-yellow-300 text-xs rounded">Private</span>
            )}
          </div>
          {repo.description && (
            <p className="text-sm text-white/60 mt-1 line-clamp-1">{repo.description}</p>
          )}
          <div className="flex items-center gap-4 mt-2 text-xs text-white/50">
            {repo.language && (
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-blue-400" />
                {repo.language}
              </span>
            )}
            <span>⭐ {repo.stars_count}</span>
            <span>🍴 {repo.forks_count}</span>
            <span>📋 {repo.open_issues_count} issues</span>
          </div>
        </div>
        
        <div className="flex items-center gap-2 ml-4">
          <button
            onClick={loadIssues}
            className="px-3 py-1.5 bg-white/10 hover:bg-white/20 text-white text-sm rounded transition-colors"
          >
            {expanded ? "Hide" : "Show"} Issues
          </button>
          <button
            onClick={onToggleSync}
            className={`px-3 py-1.5 text-sm rounded transition-colors ${
              repo.is_synced 
                ? "bg-green-500/20 text-green-300 hover:bg-green-500/30" 
                : "bg-white/10 text-white/60 hover:bg-white/20"
            }`}
          >
            {repo.is_synced ? "Syncing" : "Paused"}
          </button>
        </div>
      </div>
      
      {expanded && (
        <div className="mt-4 pt-4 border-t border-white/10">
          {loadingIssues ? (
            <div className="text-sm text-white/60">Loading issues...</div>
          ) : issues.length === 0 ? (
            <div className="text-sm text-white/60">No issues found</div>
          ) : (
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {issues.map(issue => (
                <a
                  key={issue.id}
                  href={issue.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-start gap-3 p-2 rounded hover:bg-white/5 transition-colors"
                >
                  <span className={`text-xs font-medium px-2 py-0.5 rounded ${
                    issue.state === "open" 
                      ? "bg-green-500/20 text-green-300" 
                      : "bg-purple-500/20 text-purple-300"
                  }`}>
                    #{issue.number}
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm text-white truncate">{issue.title}</div>
                    <div className="flex items-center gap-2 mt-1">
                      {issue.labels?.slice(0, 3).map((label: any) => (
                        <span 
                          key={label.name}
                          className="px-1.5 py-0.5 text-xs rounded"
                          style={{ backgroundColor: `#${label.color}20`, color: `#${label.color}` }}
                        >
                          {label.name}
                        </span>
                      ))}
                    </div>
                  </div>
                </a>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}