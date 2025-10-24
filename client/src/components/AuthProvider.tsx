// client/src/components/AuthProvider.tsx
"use client";

import React, { createContext, useContext, useEffect, useState } from "react";

type AuthContextType = {
  isAuthenticated: boolean;
  user: any | null;
  login: () => Promise<void>;
  logout: () => void;
  getToken: () => Promise<string | null>;
};

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [client, setClient] = useState<any | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState<any | null>(null);

  useEffect(() => {
    let mounted = true;

    (async () => {
      try {
        const auth0Mod = await import("@auth0/auth0-spa-js");
        const createAuth0Client = auth0Mod?.default ?? auth0Mod?.createAuth0Client;
        if (!createAuth0Client) {
          console.error("Auth0 client factory not found.");
          return;
        }

        const auth0 = await createAuth0Client({
          domain: process.env.NEXT_PUBLIC_AUTH0_DOMAIN!,
          client_id: process.env.NEXT_PUBLIC_AUTH0_CLIENT_ID!,
          authorizationParams: {
            redirect_uri: process.env.NEXT_PUBLIC_AUTH0_REDIRECT_URI,
            audience: process.env.NEXT_PUBLIC_AUTH0_AUDIENCE,
          },
          cacheLocation: "localstorage",
        });

        if (!mounted) return;
        setClient(auth0);

        if (typeof window !== "undefined" && window.location.search.includes("code=") && window.location.search.includes("state=")) {
          try {
            await auth0.handleRedirectCallback();
            window.history.replaceState({}, document.title, window.location.pathname);
          } catch (e) {
            console.error("Auth callback error", e);
          }
        }

        const auth = await auth0.isAuthenticated();
        if (!mounted) return;
        setIsAuthenticated(auth);

        if (auth) {
          const u = await auth0.getUser();
          setUser(u ?? null);
        } else {
          setUser(null);
        }
      } catch (err) {
        console.error("Failed to load auth0-spa-js:", err);
      }
    })();

    return () => {
      mounted = false;
    };
  }, []);

  async function login() {
    if (!client) return;
    await client.loginWithRedirect();
  }

  function logout() {
    if (!client) return;
    client.logout({ logoutParams: { returnTo: window.location.origin } });
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
    <AuthContext.Provider value={{ isAuthenticated, user, login, logout, getToken }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
