// client/src/contexts/AuthContext.tsx
"use client";

import React, { createContext, useEffect, useState, ReactNode } from "react";
import type { Auth0Client } from "@auth0/auth0-spa-js";
import { User } from "../types";

interface AuthContextType {
  isAuthenticated: boolean;
  isLoading: boolean;
  user: User | null;
  login: () => Promise<void>;
  logout: () => void;
  getToken: () => Promise<string | null>;
}

export const AuthContext = createContext<AuthContextType | null>(null);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [client, setClient] = useState<Auth0Client | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    let mounted = true;

    (async () => {
      try {
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

        const isAuth = await auth0.isAuthenticated();
        if (!mounted) return;
        setIsAuthenticated(isAuth);

        if (isAuth) {
          const userData = await auth0.getUser();
          setUser(userData as User ?? null);
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
        returnTo: window.location.origin,
      },
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