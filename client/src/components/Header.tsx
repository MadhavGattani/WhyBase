// client/src/components/Header.tsx
"use client";
<<<<<<< HEAD

import React, { useState } from "react";
import AuthButton from "./AuthButton";
import OrganizationSwitcher from "./OrganizationSwitcher";
import OrganizationCreator from "./OrganizationCreator";
import OrganizationManager from "./OrganizationManager";
import { useAuth } from "./AuthProvider";
import { useOrganization } from "./OrganizationProvider";
=======
import AuthButton from "./AuthButton";
>>>>>>> d0678fe (chore: push all project files to GitHub)

export default function Header() {
  const [showCreator, setShowCreator] = useState(false);
  const [showManager, setShowManager] = useState(false);
  const { isAuthenticated } = useAuth();
  const { currentOrganization, switchOrganization } = useOrganization();

  const handleOrganizationChange = (org: any) => {
    switchOrganization(org.id);
  };

  return (
    <header className="w-full bg-gradient-to-r from-primary to-indigo-700 text-white p-4">
      <div className="mx-auto max-w-6xl flex items-center justify-between">
<<<<<<< HEAD
        {/* Logo and Brand */}
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-white/10 flex items-center justify-center font-bold">L</div>
            <div className="font-semibold">Loominal</div>
          </div>

          {/* Organization Switcher - Only show when authenticated */}
          {isAuthenticated && (
            <div className="hidden md:flex items-center gap-4">
              <div className="w-px h-6 bg-white/20"></div>
              <OrganizationSwitcher
                currentOrganization={currentOrganization}
                onOrganizationChange={handleOrganizationChange}
                onCreateNew={() => setShowCreator(true)}
              />
              
              {/* Quick Settings Button */}
              {currentOrganization && !currentOrganization.is_personal && (
                <button
                  onClick={() => setShowManager(true)}
                  className="p-2 rounded-lg bg-white/10 hover:bg-white/20 transition-colors"
                  title="Organization Settings"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                </button>
              )}
            </div>
          )}
        </div>

        {/* Right Side - Auth and Mobile Menu */}
        <div className="flex items-center gap-3">
          {/* Mobile Organization Selector */}
          {isAuthenticated && (
            <div className="md:hidden">
              <button
                onClick={() => setShowCreator(true)}
                className="p-2 rounded-lg bg-white/10 hover:bg-white/20 transition-colors"
                title="Switch Organization"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                </svg>
              </button>
            </div>
          )}

=======
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-white/10 flex items-center justify-center font-bold">L</div>
          <div className="font-semibold">Loominal</div>
        </div>
        <div>
>>>>>>> d0678fe (chore: push all project files to GitHub)
          <AuthButton />
        </div>
      </div>

      {/* Mobile Organization Info */}
      {isAuthenticated && currentOrganization && (
        <div className="md:hidden mt-3 pt-3 border-t border-white/10">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-6 h-6 rounded bg-white/10 flex items-center justify-center">
                {currentOrganization.is_personal ? (
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                ) : (
                  <span className="text-xs font-medium">
                    {currentOrganization.name.charAt(0).toUpperCase()}
                  </span>
                )}
              </div>
              <div>
                <div className="text-sm font-medium">{currentOrganization.name}</div>
                <div className="text-xs text-white/70">
                  {currentOrganization.is_personal ? "Personal" : `${currentOrganization.member_count} members`}
                </div>
              </div>
            </div>
            <div className="flex gap-2">
              <OrganizationSwitcher
                currentOrganization={currentOrganization}
                onOrganizationChange={handleOrganizationChange}
                onCreateNew={() => setShowCreator(true)}
              />
              {!currentOrganization.is_personal && (
                <button
                  onClick={() => setShowManager(true)}
                  className="p-1.5 rounded bg-white/10 hover:bg-white/20 transition-colors"
                >
                  <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Modals */}
      <OrganizationCreator
        isOpen={showCreator}
        onClose={() => setShowCreator(false)}
        onSuccess={() => {
          // Organization will be automatically set as current by the provider
          setShowCreator(false);
        }}
      />

      <OrganizationManager
        isOpen={showManager}
        onClose={() => setShowManager(false)}
      />
    </header>
  );
}