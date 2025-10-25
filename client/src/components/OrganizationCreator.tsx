// client/src/components/OrganizationCreator.tsx
"use client";

import React, { useState } from "react";
import { useAuth } from "./AuthProvider";
import { useToast } from "./ToastProvider";

interface OrganizationCreatorProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: (organization: any) => void;
}

export default function OrganizationCreator({ isOpen, onClose, onSuccess }: OrganizationCreatorProps) {
  const [formData, setFormData] = useState({
    name: "",
    description: "",
    website: "",
    planType: "free"
  });
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  
  const { getToken } = useAuth();
  const toast = useToast();
  const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:5000";

  if (!isOpen) return null;

  const validateForm = () => {
    const newErrors: Record<string, string> = {};
    
    if (!formData.name.trim()) {
      newErrors.name = "Organization name is required";
    } else if (formData.name.trim().length < 2) {
      newErrors.name = "Organization name must be at least 2 characters";
    } else if (formData.name.trim().length > 100) {
      newErrors.name = "Organization name must be less than 100 characters";
    }

    if (formData.description && formData.description.length > 500) {
      newErrors.description = "Description must be less than 500 characters";
    }

    if (formData.website && formData.website.trim()) {
      const urlPattern = /^https?:\/\/.+/;
      if (!urlPattern.test(formData.website.trim())) {
        newErrors.website = "Website must be a valid URL starting with http:// or https://";
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const generateSlug = (name: string) => {
    return name
      .toLowerCase()
      .trim()
      .replace(/[^a-z0-9\s-]/g, '') // Remove special characters
      .replace(/\s+/g, '-') // Replace spaces with hyphens
      .replace(/-+/g, '-') // Replace multiple hyphens with single
      .substring(0, 50); // Limit length
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setIsLoading(true);
    try {
      const headers: any = { "Content-Type": "application/json" };
      if (getToken) {
        const token = await getToken();
        if (token) headers["Authorization"] = `Bearer ${token}`;
      }

      const organizationData = {
        name: formData.name.trim(),
        slug: generateSlug(formData.name),
        description: formData.description.trim() || null,
        website: formData.website.trim() || null,
        plan_type: formData.planType
      };

      const response = await fetch(`${API}/api/organizations`, {
        method: "POST",
        headers,
        body: JSON.stringify(organizationData)
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: "Failed to create organization" }));
        throw new Error(errorData.error || "Failed to create organization");
      }

      const result = await response.json();
      
      toast.push("Organization created successfully!", "success");
      
      // Reset form
      setFormData({
        name: "",
        description: "",
        website: "",
        planType: "free"
      });
      setErrors({});
      
      // Call success callback
      if (onSuccess) {
        onSuccess(result.organization);
      }
      
      onClose();
      
    } catch (error: any) {
      console.error("Error creating organization:", error);
      toast.push(error.message || "Failed to create organization", "error");
    } finally {
      setIsLoading(false);
    }
  };

  const handleClose = () => {
    if (!isLoading) {
      setFormData({
        name: "",
        description: "",
        website: "",
        planType: "free"
      });
      setErrors({});
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 animate-fadeIn">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={handleClose}
      />

      {/* Modal */}
      <div className="relative w-full max-w-lg bg-gradient-to-br from-slate-900 to-slate-800 rounded-2xl shadow-2xl border border-white/10 overflow-hidden animate-slideUp">
        {/* Decorative gradient orb */}
        <div className="absolute top-0 right-0 w-64 h-64 bg-primary/20 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2" />
        
        {/* Close button */}
        <button
          onClick={handleClose}
          disabled={isLoading}
          className="absolute top-4 right-4 z-10 w-8 h-8 flex items-center justify-center rounded-full bg-white/5 hover:bg-white/10 transition-colors text-white/60 hover:text-white disabled:opacity-50"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        <div className="relative p-8">
          {/* Header */}
          <div className="flex items-center gap-4 mb-6">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary to-indigo-600 flex items-center justify-center shadow-lg shadow-primary/50">
              <svg className="w-7 h-7 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
              </svg>
            </div>
            <div>
              <h2 className="text-2xl font-bold text-white">
                Create Organization
              </h2>
              <p className="text-white/60">
                Set up a new workspace for your team
              </p>
            </div>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Organization Name */}
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-white mb-2">
                Organization Name <span className="text-red-400">*</span>
              </label>
              <input
                type="text"
                id="name"
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                className={`w-full px-4 py-3 rounded-xl bg-white/5 border ${
                  errors.name ? 'border-red-500' : 'border-white/10'
                } text-white placeholder-white/50 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-colors`}
                placeholder="Enter organization name"
                disabled={isLoading}
                maxLength={100}
              />
              {errors.name && (
                <p className="mt-1 text-sm text-red-400">{errors.name}</p>
              )}
              {formData.name && (
                <p className="mt-1 text-xs text-white/50">
                  URL: {generateSlug(formData.name) || "organization-url"}
                </p>
              )}
            </div>

            {/* Description */}
            <div>
              <label htmlFor="description" className="block text-sm font-medium text-white mb-2">
                Description
              </label>
              <textarea
                id="description"
                value={formData.description}
                onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                rows={3}
                className={`w-full px-4 py-3 rounded-xl bg-white/5 border ${
                  errors.description ? 'border-red-500' : 'border-white/10'
                } text-white placeholder-white/50 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-colors resize-none`}
                placeholder="Brief description of your organization (optional)"
                disabled={isLoading}
                maxLength={500}
              />
              {errors.description && (
                <p className="mt-1 text-sm text-red-400">{errors.description}</p>
              )}
              <p className="mt-1 text-xs text-white/50">
                {formData.description.length}/500 characters
              </p>
            </div>

            {/* Website */}
            <div>
              <label htmlFor="website" className="block text-sm font-medium text-white mb-2">
                Website
              </label>
              <input
                type="url"
                id="website"
                value={formData.website}
                onChange={(e) => setFormData(prev => ({ ...prev, website: e.target.value }))}
                className={`w-full px-4 py-3 rounded-xl bg-white/5 border ${
                  errors.website ? 'border-red-500' : 'border-white/10'
                } text-white placeholder-white/50 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-colors`}
                placeholder="https://yourorganization.com (optional)"
                disabled={isLoading}
              />
              {errors.website && (
                <p className="mt-1 text-sm text-red-400">{errors.website}</p>
              )}
            </div>

            {/* Plan Type */}
            <div>
              <label htmlFor="planType" className="block text-sm font-medium text-white mb-2">
                Plan Type
              </label>
              <select
                id="planType"
                value={formData.planType}
                onChange={(e) => setFormData(prev => ({ ...prev, planType: e.target.value }))}
                className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-colors"
                disabled={isLoading}
              >
                <option value="free">Free Plan</option>
                <option value="pro">Pro Plan</option>
                <option value="enterprise">Enterprise Plan</option>
              </select>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading || !formData.name.trim()}
              className="w-full bg-gradient-to-r from-primary to-indigo-600 hover:from-primary/90 hover:to-indigo-600/90 text-white font-medium py-3.5 px-6 rounded-xl transition-all duration-200 shadow-lg shadow-primary/30 hover:shadow-xl hover:shadow-primary/40 hover:-translate-y-0.5 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none flex items-center justify-center gap-2"
            >
              {isLoading ? (
                <>
                  <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <span>Creating Organization...</span>
                </>
              ) : (
                <>
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                  </svg>
                  <span>Create Organization</span>
                </>
              )}
            </button>
          </form>

          {/* Footer */}
          <div className="mt-6 p-4 bg-white/5 rounded-xl">
            <div className="flex items-start gap-3">
              <div className="w-5 h-5 rounded-full bg-blue-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                <svg className="w-3 h-3 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div className="text-sm text-white/70">
                You'll be the owner of this organization and can invite team members, manage settings, and control access permissions.
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}