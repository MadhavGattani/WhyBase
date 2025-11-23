// client/src/contexts/OrganizationContext.tsx
"use client";

import React, { createContext, useState, useEffect, ReactNode, useRef } from "react";
import { Organization } from "../types";
import { useAuth } from "../hooks/useAuth";
import { useToast } from "../hooks/useToast";
import * as orgApi from "../services/endpoints/organizations";

interface OrganizationContextType {
  currentOrganization: Organization | null;
  organizations: Organization[];
  isLoading: boolean;
  switchOrganization: (orgId: number) => Promise<void>;
  refreshOrganizations: () => Promise<void>;
  createOrganization: (data: CreateOrganizationData) => Promise<Organization>;
}

interface CreateOrganizationData {
  name: string;
  slug: string;
  description?: string;
  website?: string;
  plan_type?: string;
}

export const OrganizationContext = createContext<OrganizationContextType | null>(null);

interface OrganizationProviderProps {
  children: ReactNode;
}

// Safe localStorage wrapper
const safeLocalStorage = {
  getItem: (key: string): string | null => {
    try {
      return localStorage.getItem(key);
    } catch (error) {
      console.warn("localStorage.getItem failed:", error);
      return null;
    }
  },
  setItem: (key: string, value: string): boolean => {
    try {
      localStorage.setItem(key, value);
      return true;
    } catch (error) {
      console.warn("localStorage.setItem failed:", error);
      return false;
    }
  },
  removeItem: (key: string): boolean => {
    try {
      localStorage.removeItem(key);
      return true;
    } catch (error) {
      console.warn("localStorage.removeItem failed:", error);
      return false;
    }
  }
};

export function OrganizationProvider({ children }: OrganizationProviderProps) {
  const [currentOrganization, setCurrentOrganization] = useState<Organization | null>(null);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // ✅ Add AbortController ref
  const abortControllerRef = useRef<AbortController | null>(null);

  const { isAuthenticated, getToken } = useAuth();
  const toast = useToast();

  useEffect(() => {
    const savedOrgId = safeLocalStorage.getItem("currentOrganizationId");
    if (savedOrgId && isAuthenticated) {
      // Will be loaded when organizations are fetched
    }
  }, [isAuthenticated]);

  useEffect(() => {
    if (isAuthenticated) {
      refreshOrganizations();
    } else {
      setCurrentOrganization(null);
      setOrganizations([]);
      setIsLoading(false);
    }

    // ✅ Cleanup on unmount
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [isAuthenticated]);

  const refreshOrganizations = async (): Promise<void> => {
    if (!isAuthenticated) return;

    // ✅ Cancel previous request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // ✅ Create new AbortController
    abortControllerRef.current = new AbortController();

    setIsLoading(true);
    try {
      const token = await getToken();
      
      // Note: You'd need to update your API client to accept signal
      const data = await orgApi.getOrganizations({ token });
      
      // ✅ Check if request was aborted
      if (abortControllerRef.current?.signal.aborted) {
        return;
      }

      const orgs = data.organizations || [];
      setOrganizations(orgs);

      const savedOrgId = safeLocalStorage.getItem("currentOrganizationId");
      let targetOrg: Organization | null = null;

      if (savedOrgId) {
        targetOrg = orgs.find((org: Organization) => org.id === parseInt(savedOrgId)) || null;
      }

      if (!targetOrg) {
        targetOrg = orgs.find((org: Organization) => org.is_personal) || orgs[0] || null;
      }

      setCurrentOrganization(targetOrg);

      if (targetOrg) {
        safeLocalStorage.setItem("currentOrganizationId", targetOrg.id.toString());
      }
    } catch (error: any) {
      // ✅ Don't show error for aborted requests
      if (error.name === 'AbortError') {
        return;
      }
      console.error("Error fetching organizations:", error);
      toast.push("Failed to load organizations", "error");
    } finally {
      setIsLoading(false);
    }
  };

  const switchOrganization = async (orgId: number): Promise<void> => {
    const org = organizations.find((o) => o.id === orgId);
    if (!org) {
      toast.push("Organization not found", "error");
      return;
    }

    
    const previousOrg = currentOrganization;
    setCurrentOrganization(org);
    safeLocalStorage.setItem("currentOrganizationId", orgId.toString());

    try {
      // If we had an API call to confirm the switch, it would go here
      toast.push(`Switched to ${org.name}`, "success");
    } catch (error) {
      // ✅ Rollback on error
      setCurrentOrganization(previousOrg);
      if (previousOrg) {
        safeLocalStorage.setItem("currentOrganizationId", previousOrg.id.toString());
      }
      toast.push("Failed to switch organization", "error");
    }
  };

  const createOrganization = async (data: CreateOrganizationData): Promise<Organization> => {
    try {
      const token = await getToken();
      const result = await orgApi.createOrganization(data, { token });
      const newOrg = result.organization;

      setOrganizations((prev) => [...prev, newOrg]);
      setCurrentOrganization(newOrg);
      safeLocalStorage.setItem("currentOrganizationId", newOrg.id.toString());

      toast.push(`Created and switched to ${newOrg.name}`, "success");

      return newOrg;
    } catch (error: any) {
      console.error("Error creating organization:", error);
      toast.push(error.message || "Failed to create organization", "error");
      throw error;
    }
  };

  const contextValue: OrganizationContextType = {
    currentOrganization,
    organizations,
    isLoading,
    switchOrganization,
    refreshOrganizations,
    createOrganization,
  };

  return (
    <OrganizationContext.Provider value={contextValue}>{children}</OrganizationContext.Provider>
  );
}