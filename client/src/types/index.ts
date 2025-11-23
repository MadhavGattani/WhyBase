// client/src/types/index.ts

export interface User {
  id: number;
  email: string;
  name?: string;
  picture?: string;
  display_name?: string;
}

export interface Organization {
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

export interface Member {
  id: number;
  email: string;
  display_name: string;
  avatar_url?: string;
  role: 'owner' | 'admin' | 'member' | 'viewer';
  joined_at: string;
  is_active: boolean;
}

export interface Invitation {
  id: number;
  email: string;
  role: 'owner' | 'admin' | 'member' | 'viewer';
  status: 'pending' | 'accepted' | 'declined' | 'expired';
  created_at: string;
  expires_at: string;
  invited_by: {
    display_name: string;
    email: string;
  };
}

export interface Template {
  id: number;
  name: string;
  prompt: string;
  description?: string;
  is_public: boolean;
  is_organization_template: boolean;
  created_at: string;
  updated_at: string;
}

export interface Query {
  id: number;
  prompt: string;
  response: string;
  created_at: string;
}

export interface Upload {
  id: number;
  filename: string;
  size: number;
  content_type?: string;
  created_at: string;
}

export type ToastType = "info" | "success" | "error";