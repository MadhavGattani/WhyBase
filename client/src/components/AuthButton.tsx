// client/src/components/AuthButton.tsx
"use client";
import React, { useState } from "react";
import { useAuth } from "./AuthProvider";
import LoginModal from "./LoginModal";

export default function AuthButton() {
  const { isAuthenticated, isLoading, user, logout } = useAuth();
  const [showLoginModal, setShowLoginModal] = useState(false);

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-white/60">
        <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <span className="text-sm">Loading...</span>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <>
        <button
          onClick={() => setShowLoginModal(true)}
          className="px-5 py-2.5 rounded-lg bg-white text-primary font-medium hover:bg-white/90 transition-all duration-200 shadow-lg hover:shadow-xl hover:-translate-y-0.5 flex items-center gap-2"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1" />
          </svg>
          <span>Sign In</span>
        </button>
        <LoginModal isOpen={showLoginModal} onClose={() => setShowLoginModal(false)} />
      </>
    );
  }

  return (
    <div className="flex items-center gap-3">
      {/* User Avatar & Name */}
      <div className="flex items-center gap-3 px-3 py-1.5 rounded-lg bg-white/10">
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary to-indigo-600 flex items-center justify-center text-white font-medium text-sm shadow-lg">
          {user?.picture ? (
            <img 
              src={user.picture} 
              alt={user.name || "User"} 
              className="w-full h-full rounded-full object-cover"
            />
          ) : (
            <span>{(user?.name || user?.email || "U").charAt(0).toUpperCase()}</span>
          )}
        </div>
        <div className="hidden sm:block">
          <div className="text-sm font-medium text-white">
            {user?.name || user?.email || "User"}
          </div>
          {user?.email && user?.name && (
            <div className="text-xs text-white/60">{user.email}</div>
          )}
        </div>
      </div>

      {/* Logout Button */}
      <button
        onClick={logout}
        className="px-4 py-2 rounded-lg bg-white/10 hover:bg-white/20 text-white transition-all duration-200 flex items-center gap-2 group"
        title="Sign out"
      >
        <svg 
          className="w-4 h-4 group-hover:rotate-12 transition-transform" 
          fill="none" 
          viewBox="0 0 24 24" 
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
        </svg>
        <span className="hidden md:inline text-sm">Sign Out</span>
      </button>
    </div>
  );
}