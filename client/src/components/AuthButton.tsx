// client/src/components/AuthButton.tsx
"use client";
import React from "react";
import { useAuth } from "./AuthProvider";

export default function AuthButton() {
  const { isAuthenticated, user, login, logout } = useAuth();

  if (!isAuthenticated) {
    return <button onClick={login} className="px-3 py-1 rounded bg-primary text-white">Log in</button>;
  }
  return (
    <div className="flex items-center gap-3 text-white">
      <div className="text-sm">Hi, {user?.name ?? user?.email ?? "User"}</div>
      <button onClick={logout} className="px-3 py-1 rounded bg-white/10">Log out</button>
    </div>
  );
}
