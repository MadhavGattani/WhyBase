// client/src/components/OrganizationProvider.tsx
"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { useAuth } from "./AuthProvider";
import { useToast } from "./ToastProvider";

interface Organization {
  id: number;
  name: string;
  slug: string;
  description?: string;
  logo_url?: string;
  is_personal: boolean;
  is_active: boolean;
  member_count: number;
  plan_type: string;
  created_at: string;
  updated_at: string;
}

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

const OrganizationContext = createContext<OrganizationContextType | null>(null);

export function OrganizationProvider({ children }: { children: ReactNode }) {
  const [currentOrganization, setCurrentOrganization] = useState<Organization | null>(null);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  
  const { isAuthenticated, getToken } = useAuth();
  const toast = useToast();
  const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:5000";

  // Load saved organization preference
  useEffect(() => {
    const savedOrgId = localStorage.getItem('currentOrganizationId');
    if (savedOrgId && isAuthenticated) {
      // Will be loaded when organizations are fetched
    }
  }, [isAuthenticated]);

  // Fetch organizations when user is authenticated
  useEffect(() => {
    if (isAuthenticated) {
      refreshOrganizations();
    } else {
      setCurrentOrganization(null);
      setOrganizations([]);
      setIsLoading(false);
    }
  }, [isAuthenticated]);

  const refreshOrganizations = async (): Promise<void> => {
    if (!isAuthenticated) return;
    
    setIsLoading(true);
    try {
      const headers: any = {};
      if (getToken) {
        const token = await getToken();
        if (token) headers["Authorization"] = `Bearer ${token}`;
      }

      const response = await fetch(`${API}/api/organizations`, { headers });
      if (!response.ok) {
        throw new Error("Failed to fetch organizations");
      }

      const data = await response.json();
      const orgs = data.organizations || [];
      setOrganizations(orgs);

      // Set current organization
      const savedOrgId = localStorage.getItem('currentOrganizationId');
      let targetOrg: Organization | null = null;

      if (savedOrgId) {
        targetOrg = orgs.find((org: Organization) => org.id === parseInt(savedOrgId));
      }

      // If no saved org or saved org not found, use personal org or first available
      if (!targetOrg) {
        targetOrg = orgs.find((org: Organization) => org.is_personal) || orgs[0] || null;
      }

      setCurrentOrganization(targetOrg);
      
      // Save current organization ID
      if (targetOrg) {
        localStorage.setItem('currentOrganizationId', targetOrg.id.toString());
      }

    } catch (error: any) {
      console.error("Error fetching organizations:", error);
      toast.push("Failed to load organizations", "error");
    } finally {
      setIsLoading(false);
    }
  };

  const switchOrganization = async (orgId: number): Promise<void> => {
    const org = organizations.find(o => o.id === orgId);
    if (!org) {
      toast.push("Organization not found", "error");
      return;
    }

    setCurrentOrganization(org);
    localStorage.setItem('currentOrganizationId', orgId.toString());
    
    toast.push(`Switched to ${org.name}`, "success");
  };

  const createOrganization = async (data: CreateOrganizationData): Promise<Organization> => {
    try {
      const headers: any = { "Content-Type": "application/json" };
      if (getToken) {
        const token = await getToken();
        if (token) headers["Authorization"] = `Bearer ${token}`;
      }

      const response = await fetch(`${API}/api/organizations`, {
        method: "POST",
        headers,
        body: JSON.stringify(data)
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: "Failed to create organization" }));
        throw new Error(errorData.error || "Failed to create organization");
      }

      const result = await response.json();
      const newOrg = result.organization;

      // Add to organizations list
      setOrganizations(prev => [...prev, newOrg]);
      
      // Switch to the new organization
      setCurrentOrganization(newOrg);
      localStorage.setItem('currentOrganizationId', newOrg.id.toString());
      
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
    createOrganization
  };

  return (
    <OrganizationContext.Provider value={contextValue}>
      {children}
    </OrganizationContext.Provider>
  );
}

export function useOrganization() {
  const context = useContext(OrganizationContext);
  if (!context) {
    throw new Error("useOrganization must be used within OrganizationProvider");
  }
  return context;
}