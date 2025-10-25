// client/src/components/AuthProvider.tsx
"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import type { Auth0Client } from "@auth0/auth0-spa-js";

type AuthContextType = {
  isAuthenticated: boolean;
  isLoading: boolean;
  user: any | null;
  login: () => Promise<void>;
  logout: () => void;
  getToken: () => Promise<string | null>;
};

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [client, setClient] = useState<Auth0Client | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [user, setUser] = useState<any | null>(null);

  useEffect(() => {
    let mounted = true;

    (async () => {
      try {
        // Import Auth0 client
        const { createAuth0Client } = await import("@auth0/auth0-spa-js");

        const auth0 = await createAuth0Client({
          domain: process.env.NEXT_PUBLIC_AUTH0_DOMAIN!,
          clientId: process.env.NEXT_PUBLIC_AUTH0_CLIENT_ID!,
          authorizationParams: {
            redirect_uri: process.env.NEXT_PUBLIC_AUTH0_REDIRECT_URI,
            audience: process.env.NEXT_PUBLIC_AUTH0_AUDIENCE,
          },
          cacheLocation: "localstorage",
        });

        if (!mounted) return;
        setClient(auth0);

        // Handle redirect callback
        if (
          typeof window !== "undefined" &&
          window.location.search.includes("code=") &&
          window.location.search.includes("state=")
        ) {
          try {
            await auth0.handleRedirectCallback();
            window.history.replaceState({}, document.title, window.location.pathname);
          } catch (e) {
            console.error("Auth callback error", e);
          }
        }

        // Check authentication status
        const isAuth = await auth0.isAuthenticated();
        if (!mounted) return;
        setIsAuthenticated(isAuth);

        if (isAuth) {
          const userData = await auth0.getUser();
          setUser(userData ?? null);
        } else {
          setUser(null);
        }

        setIsLoading(false);
      } catch (err) {
        console.error("Failed to initialize Auth0:", err);
        setIsLoading(false);
      }
    })();

    return () => {
      mounted = false;
    };
  }, []);

  async function login() {
    if (!client) return;
    try {
      await client.loginWithRedirect();
    } catch (error) {
      console.error("Login error:", error);
    }
  }

  function logout() {
    if (!client) return;
    client.logout({ 
      logoutParams: { 
        returnTo: window.location.origin 
      } 
    });
  }

  async function getToken() {
    if (!client) return null;
    try {
      const token = await client.getTokenSilently();
      return token;
    } catch (e) {
      console.warn("getToken error", e);
      return null;
    }
  }

  return (
    <AuthContext.Provider value={{ isAuthenticated, isLoading, user, login, logout, getToken }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}