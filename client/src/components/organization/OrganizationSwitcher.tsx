// client/src/components/OrganizationSwitcher.tsx
"use client";

import React, { useState, useEffect, useRef } from "react";
import { useAuth } from "../../hooks/useAuth";
import { useToast } from "../../hooks/useToast";

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
}

interface OrganizationSwitcherProps {
  currentOrganization?: Organization | null;
  onOrganizationChange: (org: Organization) => void;
  onCreateNew: () => void;
}

export default function OrganizationSwitcher({
  currentOrganization,
  onOrganizationChange,
  onCreateNew
}: OrganizationSwitcherProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [loading, setLoading] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  
  const { getToken } = useAuth();
  const toast = useToast();
  const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:5000";

  useEffect(() => {
    if (isOpen) {
      fetchOrganizations();
    }
  }, [isOpen]);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const fetchOrganizations = async () => {
    setLoading(true);
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
      setOrganizations(data.organizations || []);
    } catch (error: any) {
      console.error("Error fetching organizations:", error);
      toast.push("Failed to load organizations", "error");
    } finally {
      setLoading(false);
    }
  };

  const handleOrganizationSelect = (org: Organization) => {
    onOrganizationChange(org);
    setIsOpen(false);
  };

  const getOrganizationIcon = (org: Organization) => {
    if (org.logo_url) {
      return (
        <img
          src={org.logo_url}
          alt={org.name}
          className="w-8 h-8 rounded-lg object-cover"
        />
      );
    }

    if (org.is_personal) {
      return (
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center">
          <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
          </svg>
        </div>
      );
    }

    return (
      <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-indigo-600 flex items-center justify-center">
        <span className="text-white font-medium text-sm">
          {org.name.charAt(0).toUpperCase()}
        </span>
      </div>
    );
  };

  const getPlanBadge = (planType: string) => {
    const planColors = {
      free: "bg-gray-500/20 text-gray-300",
      pro: "bg-blue-500/20 text-blue-300",
      enterprise: "bg-purple-500/20 text-purple-300"
    };

    return (
      <span className={`px-2 py-1 rounded text-xs font-medium ${planColors[planType as keyof typeof planColors] || planColors.free}`}>
        {planType.charAt(0).toUpperCase() + planType.slice(1)}
      </span>
    );
  };

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Current Organization Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-3 px-4 py-2.5 rounded-xl bg-white/10 hover:bg-white/20 transition-all duration-200 min-w-0 max-w-64"
      >
        {currentOrganization ? (
          <>
            {getOrganizationIcon(currentOrganization)}
            <div className="flex-1 min-w-0 text-left">
              <div className="text-white font-medium truncate">
                {currentOrganization.name}
              </div>
              <div className="text-white/60 text-xs truncate">
                {currentOrganization.is_personal ? "Personal" : `${currentOrganization.member_count} members`}
              </div>
            </div>
          </>
        ) : (
          <>
            <div className="w-8 h-8 rounded-lg bg-white/10 flex items-center justify-center">
              <svg className="w-5 h-5 text-white/60" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
              </svg>
            </div>
            <div className="text-left">
              <div className="text-white font-medium">Select Organization</div>
              <div className="text-white/60 text-xs">Choose workspace</div>
            </div>
          </>
        )}
        
        <svg
          className={`w-4 h-4 text-white/60 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute top-full left-0 right-0 mt-2 bg-slate-800/95 backdrop-blur-sm rounded-xl shadow-2xl border border-white/10 overflow-hidden z-50 animate-slideDown max-h-96 overflow-y-auto">
          {loading ? (
            <div className="p-4 text-center">
              <svg className="animate-spin h-6 w-6 text-white/60 mx-auto" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <p className="text-white/60 text-sm mt-2">Loading organizations...</p>
            </div>
          ) : (
            <>
              {/* Organizations List */}
              <div className="max-h-64 overflow-y-auto">
                {organizations.length === 0 ? (
                  <div className="p-4 text-center">
                    <div className="w-12 h-12 rounded-full bg-white/5 flex items-center justify-center mx-auto mb-3">
                      <svg className="w-6 h-6 text-white/60" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                      </svg>
                    </div>
                    <p className="text-white/60 text-sm">No organizations found</p>
                    <p className="text-white/40 text-xs mt-1">Create your first organization to get started</p>
                  </div>
                ) : (
                  organizations.map((org) => (
                    <button
                      key={org.id}
                      onClick={() => handleOrganizationSelect(org)}
                      className={`w-full flex items-center gap-3 px-4 py-3 hover:bg-white/10 transition-colors ${
                        currentOrganization?.id === org.id ? 'bg-white/5' : ''
                      }`}
                    >
                      {getOrganizationIcon(org)}
                      <div className="flex-1 min-w-0 text-left">
                        <div className="flex items-center gap-2">
                          <span className="text-white font-medium truncate">
                            {org.name}
                          </span>
                          {currentOrganization?.id === org.id && (
                            <svg className="w-4 h-4 text-primary flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                            </svg>
                          )}
                        </div>
                        <div className="flex items-center gap-2 text-xs text-white/60">
                          <span>
                            {org.is_personal ? "Personal workspace" : `${org.member_count} members`}
                          </span>
                          {getPlanBadge(org.plan_type)}
                        </div>
                        {org.description && (
                          <p className="text-xs text-white/40 truncate mt-1">
                            {org.description}
                          </p>
                        )}
                      </div>
                    </button>
                  ))
                )}
              </div>

              {/* Divider */}
              <div className="border-t border-white/10"></div>

              {/* Create New Organization Button */}
              <button
                onClick={() => {
                  setIsOpen(false);
                  onCreateNew();
                }}
                className="w-full flex items-center gap-3 px-4 py-3 hover:bg-white/10 transition-colors text-left"
              >
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-indigo-600 flex items-center justify-center">
                  <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                  </svg>
                </div>
                <div>
                  <div className="text-white font-medium">Create Organization</div>
                  <div className="text-white/60 text-xs">Set up a new workspace</div>
                </div>
              </button>
            </>
          )}
        </div>
      )}
    </div>
  );
}