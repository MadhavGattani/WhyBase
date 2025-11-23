// client/src/services/endpoints/organizations.ts

import { apiRequest, ApiOptions } from "../api";
import { Organization, Member, Invitation } from "../../types";

export async function getOrganizations(options: ApiOptions = {}): Promise<{ organizations: Organization[] }> {
  return apiRequest("/api/organizations", options);
}

export async function createOrganization(
  data: {
    name: string;
    slug: string;
    description?: string;
    website?: string;
    plan_type?: string;
  },
  options: ApiOptions = {}
): Promise<{ organization: Organization }> {
  return apiRequest("/api/organizations", {
    method: "POST",
    body: JSON.stringify(data),
    ...options,
  });
}

export async function updateOrganization(
  id: number,
  data: Partial<Organization>,
  options: ApiOptions = {}
): Promise<{ organization: Organization }> {
  return apiRequest(`/api/organizations/${id}`, {
    method: "PUT",
    body: JSON.stringify(data),
    ...options,
  });
}

export async function getOrganizationMembers(
  id: number,
  options: ApiOptions = {}
): Promise<{ members: Member[] }> {
  return apiRequest(`/api/organizations/${id}/members`, options);
}

export async function updateMemberRole(
  orgId: number,
  memberId: number,
  role: string,
  options: ApiOptions = {}
): Promise<{ message: string }> {
  return apiRequest(`/api/organizations/${orgId}/members/${memberId}`, {
    method: "PUT",
    body: JSON.stringify({ role }),
    ...options,
  });
}

export async function removeMember(
  orgId: number,
  memberId: number,
  options: ApiOptions = {}
): Promise<{ message: string }> {
  return apiRequest(`/api/organizations/${orgId}/members/${memberId}`, {
    method: "DELETE",
    ...options,
  });
}

export async function inviteToOrganization(
  orgId: number,
  data: { email: string; role: string; message?: string },
  options: ApiOptions = {}
): Promise<{ invitation: Invitation }> {
  return apiRequest(`/api/organizations/${orgId}/invite`, {
    method: "POST",
    body: JSON.stringify(data),
    ...options,
  });
}

export async function getInvitations(
  orgId: number,
  options: ApiOptions = {}
): Promise<{ invitations: Invitation[] }> {
  return apiRequest(`/api/organizations/${orgId}/invitations`, options);
}

export async function revokeInvitation(
  orgId: number,
  invitationId: number,
  options: ApiOptions = {}
): Promise<{ message: string }> {
  return apiRequest(`/api/organizations/${orgId}/invitations/${invitationId}`, {
    method: "DELETE",
    ...options,
  });
}