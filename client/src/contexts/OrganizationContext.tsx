// client/src/contexts/OrganizationContext.tsx
"use client";

import React, { createContext, useState, useEffect, ReactNode } from "react";
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

export function OrganizationProvider({ children }: OrganizationProviderProps) {
  const [currentOrganization, setCurrentOrganization] = useState<Organization | null>(null);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const { isAuthenticated, getToken } = useAuth();
  const toast = useToast();

  useEffect(() => {
    const savedOrgId = localStorage.getItem("currentOrganizationId");
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
  }, [isAuthenticated]);

  const refreshOrganizations = async (): Promise<void> => {
    if (!isAuthenticated) return;

    setIsLoading(true);
    try {
      const token = await getToken();
      const data = await orgApi.getOrganizations({ token });
      const orgs = data.organizations || [];
      setOrganizations(orgs);

      const savedOrgId = localStorage.getItem("currentOrganizationId");
      let targetOrg: Organization | null = null;

      if (savedOrgId) {
        targetOrg = orgs.find((org: Organization) => org.id === parseInt(savedOrgId)) || null;
      }

      if (!targetOrg) {
        targetOrg = orgs.find((org: Organization) => org.is_personal) || orgs[0] || null;
      }

      setCurrentOrganization(targetOrg);

      if (targetOrg) {
        localStorage.setItem("currentOrganizationId", targetOrg.id.toString());
      }
    } catch (error: any) {
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

    setCurrentOrganization(org);
    localStorage.setItem("currentOrganizationId", orgId.toString());

    toast.push(`Switched to ${org.name}`, "success");
  };

  const createOrganization = async (data: CreateOrganizationData): Promise<Organization> => {
    try {
      const token = await getToken();
      const result = await orgApi.createOrganization(data, { token });
      const newOrg = result.organization;

      setOrganizations((prev) => [...prev, newOrg]);
      setCurrentOrganization(newOrg);
      localStorage.setItem("currentOrganizationId", newOrg.id.toString());

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