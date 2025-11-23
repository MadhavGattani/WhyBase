// client/src/components/OrganizationManager.tsx
"use client";

import React, { useState, useEffect } from "react";
import { useOrganization } from "../../hooks/useOrganization";
import { useAuth } from "../../hooks/useAuth";
import { useToast } from "../../hooks/useToast";

interface Member {
  id: number;
  email: string;
  display_name: string;
  avatar_url?: string;
  role: 'owner' | 'admin' | 'member' | 'viewer';
  joined_at: string;
  is_active: boolean;
}

interface Invitation {
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

interface OrganizationManagerProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function OrganizationManager({ isOpen, onClose }: OrganizationManagerProps) {
  const [activeTab, setActiveTab] = useState<'settings' | 'members' | 'invitations'>('settings');
  const [members, setMembers] = useState<Member[]>([]);
  const [invitations, setInvitations] = useState<Invitation[]>([]);
  const [loading, setLoading] = useState(false);
  
  // Settings form
  const [settings, setSettings] = useState({
    name: "",
    description: "",
    website: "",
    max_members: 50
  });

  // Invite form
  const [inviteForm, setInviteForm] = useState({
    email: "",
    role: "member" as 'member' | 'admin' | 'viewer'
  });

  const { currentOrganization, refreshOrganizations } = useOrganization();
  const { getToken } = useAuth();
  const toast = useToast();
  const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:5000";

  useEffect(() => {
    if (isOpen && currentOrganization) {
      loadOrganizationData();
    }
  }, [isOpen, currentOrganization]);

  const loadOrganizationData = async () => {
    if (!currentOrganization) return;

    setSettings({
      name: currentOrganization.name,
      description: currentOrganization.description || "",
      website: "", // Will be loaded from API
      max_members: 50 // Will be loaded from API
    });

    await Promise.all([
      loadMembers(),
      loadInvitations()
    ]);
  };

  const loadMembers = async () => {
    if (!currentOrganization) return;

    try {
      const headers: any = {};
      if (getToken) {
        const token = await getToken();
        if (token) headers["Authorization"] = `Bearer ${token}`;
      }

      const response = await fetch(`${API}/api/organizations/${currentOrganization.id}/members`, { headers });
      if (response.ok) {
        const data = await response.json();
        setMembers(data.members || []);
      }
    } catch (error) {
      console.error("Error loading members:", error);
    }
  };

  const loadInvitations = async () => {
    if (!currentOrganization) return;

    try {
      const headers: any = {};
      if (getToken) {
        const token = await getToken();
        if (token) headers["Authorization"] = `Bearer ${token}`;
      }

      const response = await fetch(`${API}/api/organizations/${currentOrganization.id}/invitations`, { headers });
      if (response.ok) {
        const data = await response.json();
        setInvitations(data.invitations || []);
      }
    } catch (error) {
      console.error("Error loading invitations:", error);
    }
  };

  const updateSettings = async () => {
    if (!currentOrganization) return;

    setLoading(true);
    try {
      const headers: any = { "Content-Type": "application/json" };
      if (getToken) {
        const token = await getToken();
        if (token) headers["Authorization"] = `Bearer ${token}`;
      }

      const response = await fetch(`${API}/api/organizations/${currentOrganization.id}`, {
        method: "PUT",
        headers,
        body: JSON.stringify(settings)
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({ error: "Update failed" }));
        throw new Error(error.error || "Failed to update organization");
      }

      toast.push("Organization updated successfully", "success");
      await refreshOrganizations();
    } catch (error: any) {
      toast.push(error.message || "Failed to update organization", "error");
    } finally {
      setLoading(false);
    }
  };

  const sendInvitation = async () => {
    if (!currentOrganization || !inviteForm.email.trim()) {
      toast.push("Please enter an email address", "error");
      return;
    }

    setLoading(true);
    try {
      const headers: any = { "Content-Type": "application/json" };
      if (getToken) {
        const token = await getToken();
        if (token) headers["Authorization"] = `Bearer ${token}`;
      }

      const response = await fetch(`${API}/api/organizations/${currentOrganization.id}/invite`, {
        method: "POST",
        headers,
        body: JSON.stringify(inviteForm)
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({ error: "Invitation failed" }));
        throw new Error(error.error || "Failed to send invitation");
      }

      toast.push("Invitation sent successfully", "success");
      setInviteForm({ email: "", role: "member" });
      await loadInvitations();
    } catch (error: any) {
      toast.push(error.message || "Failed to send invitation", "error");
    } finally {
      setLoading(false);
    }
  };

  const updateMemberRole = async (memberId: number, newRole: string) => {
    if (!currentOrganization) return;

    try {
      const headers: any = { "Content-Type": "application/json" };
      if (getToken) {
        const token = await getToken();
        if (token) headers["Authorization"] = `Bearer ${token}`;
      }

      const response = await fetch(`${API}/api/organizations/${currentOrganization.id}/members/${memberId}`, {
        method: "PUT",
        headers,
        body: JSON.stringify({ role: newRole })
      });

      if (!response.ok) {
        throw new Error("Failed to update member role");
      }

      toast.push("Member role updated", "success");
      await loadMembers();
    } catch (error: any) {
      toast.push(error.message || "Failed to update member role", "error");
    }
  };

  const removeMember = async (memberId: number) => {
    if (!currentOrganization || !confirm("Are you sure you want to remove this member?")) return;

    try {
      const headers: any = {};
      if (getToken) {
        const token = await getToken();
        if (token) headers["Authorization"] = `Bearer ${token}`;
      }

      const response = await fetch(`${API}/api/organizations/${currentOrganization.id}/members/${memberId}`, {
        method: "DELETE",
        headers
      });

      if (!response.ok) {
        throw new Error("Failed to remove member");
      }

      toast.push("Member removed", "success");
      await loadMembers();
    } catch (error: any) {
      toast.push(error.message || "Failed to remove member", "error");
    }
  };

  const revokeInvitation = async (invitationId: number) => {
    if (!currentOrganization) return;

    try {
      const headers: any = {};
      if (getToken) {
        const token = await getToken();
        if (token) headers["Authorization"] = `Bearer ${token}`;
      }

      const response = await fetch(`${API}/api/organizations/${currentOrganization.id}/invitations/${invitationId}`, {
        method: "DELETE",
        headers
      });

      if (!response.ok) {
        throw new Error("Failed to revoke invitation");
      }

      toast.push("Invitation revoked", "success");
      await loadInvitations();
    } catch (error: any) {
      toast.push(error.message || "Failed to revoke invitation", "error");
    }
  };

  if (!isOpen || !currentOrganization) return null;

  const getRoleColor = (role: string) => {
    const colors = {
      owner: "text-purple-300 bg-purple-500/20",
      admin: "text-blue-300 bg-blue-500/20",
      member: "text-green-300 bg-green-500/20",
      viewer: "text-gray-300 bg-gray-500/20"
    };
    return colors[role as keyof typeof colors] || colors.member;
  };

  const canManageMembers = () => {
    // In a real app, you'd check the user's role in the organization
    return true; // For now, allow all operations
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 animate-fadeIn">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />

      {/* Modal */}
      <div className="relative w-full max-w-4xl max-h-[90vh] bg-gradient-to-br from-slate-900 to-slate-800 rounded-2xl shadow-2xl border border-white/10 overflow-hidden animate-slideUp">
        {/* Header */}
        <div className="p-6 border-b border-white/10">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary to-indigo-600 flex items-center justify-center">
                {currentOrganization.logo_url ? (
                  <img src={currentOrganization.logo_url} alt={currentOrganization.name} className="w-full h-full rounded-xl object-cover" />
                ) : (
                  <span className="text-white font-bold text-lg">
                    {currentOrganization.name.charAt(0).toUpperCase()}
                  </span>
                )}
              </div>
              <div>
                <h2 className="text-2xl font-bold text-white">{currentOrganization.name}</h2>
                <p className="text-white/60">Organization Settings</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="w-8 h-8 flex items-center justify-center rounded-full bg-white/5 hover:bg-white/10 transition-colors text-white/60 hover:text-white"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Tabs */}
          <div className="flex gap-1 mt-6 bg-white/5 rounded-lg p-1">
            {[
              { id: 'settings', label: 'Settings', icon: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z M15 12a3 3 0 11-6 0 3 3 0 016 0z' },
              { id: 'members', label: 'Members', icon: 'M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z' },
              { id: 'invitations', label: 'Invitations', icon: 'M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z' }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-md font-medium transition-colors ${
                  activeTab === tab.id
                    ? 'bg-white/10 text-white'
                    : 'text-white/60 hover:text-white hover:bg-white/5'
                }`}
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={tab.icon} />
                </svg>
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-200px)]">
          {activeTab === 'settings' && (
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-white mb-2">Organization Name</label>
                <input
                  type="text"
                  value={settings.name}
                  onChange={(e) => setSettings(prev => ({ ...prev, name: e.target.value }))}
                  className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-white/50 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                  placeholder="Enter organization name"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-white mb-2">Description</label>
                <textarea
                  value={settings.description}
                  onChange={(e) => setSettings(prev => ({ ...prev, description: e.target.value }))}
                  rows={3}
                  className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-white/50 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary resize-none"
                  placeholder="Brief description of your organization"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-white mb-2">Website</label>
                <input
                  type="url"
                  value={settings.website}
                  onChange={(e) => setSettings(prev => ({ ...prev, website: e.target.value }))}
                  className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-white/50 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                  placeholder="https://yourorganization.com"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-white mb-2">Max Members</label>
                <input
                  type="number"
                  value={settings.max_members}
                  onChange={(e) => setSettings(prev => ({ ...prev, max_members: parseInt(e.target.value) || 50 }))}
                  min="1"
                  max="1000"
                  className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-white/50 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                />
              </div>

              <button
                onClick={updateSettings}
                disabled={loading}
                className="w-full bg-gradient-to-r from-primary to-indigo-600 hover:from-primary/90 hover:to-indigo-600/90 text-white font-medium py-3 px-6 rounded-xl transition-all duration-200 disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Updating...
                  </>
                ) : (
                  'Update Settings'
                )}
              </button>
            </div>
          )}

          {activeTab === 'members' && (
            <div className="space-y-6">
              {/* Invite New Member */}
              {canManageMembers() && (
                <div className="p-4 bg-white/5 rounded-xl">
                  <h3 className="font-medium text-white mb-4">Invite New Member</h3>
                  <div className="flex gap-3">
                    <input
                      type="email"
                      value={inviteForm.email}
                      onChange={(e) => setInviteForm(prev => ({ ...prev, email: e.target.value }))}
                      className="flex-1 px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-white placeholder-white/50 focus:outline-none focus:border-primary"
                      placeholder="Enter email address"
                    />
                    <select
                      value={inviteForm.role}
                      onChange={(e) => setInviteForm(prev => ({ ...prev, role: e.target.value as any }))}
                      className="px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-white focus:outline-none focus:border-primary"
                    >
                      <option value="viewer">Viewer</option>
                      <option value="member">Member</option>
                      <option value="admin">Admin</option>
                    </select>
                    <button
                      onClick={sendInvitation}
                      disabled={loading || !inviteForm.email.trim()}
                      className="px-6 py-2 bg-primary hover:bg-primary/90 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
                    >
                      Invite
                    </button>
                  </div>
                </div>
              )}

              {/* Members List */}
              <div>
                <h3 className="font-medium text-white mb-4">Members ({members.length})</h3>
                <div className="space-y-3">
                  {members.map((member) => (
                    <div key={member.id} className="flex items-center justify-between p-4 bg-white/5 rounded-xl">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary to-indigo-600 flex items-center justify-center">
                          {member.avatar_url ? (
                            <img src={member.avatar_url} alt={member.display_name} className="w-full h-full rounded-full object-cover" />
                          ) : (
                            <span className="text-white font-medium">
                              {(member.display_name || member.email).charAt(0).toUpperCase()}
                            </span>
                          )}
                        </div>
                        <div>
                          <div className="font-medium text-white">{member.display_name || member.email}</div>
                          <div className="text-sm text-white/60">{member.email}</div>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className={`px-3 py-1 rounded-full text-xs font-medium ${getRoleColor(member.role)}`}>
                          {member.role.charAt(0).toUpperCase() + member.role.slice(1)}
                        </span>
                        {canManageMembers() && member.role !== 'owner' && (
                          <div className="flex gap-2">
                            <select
                              value={member.role}
                              onChange={(e) => updateMemberRole(member.id, e.target.value)}
                              className="px-2 py-1 rounded bg-white/10 text-white text-xs border border-white/10 focus:outline-none focus:border-primary"
                            >
                              <option value="viewer">Viewer</option>
                              <option value="member">Member</option>
                              <option value="admin">Admin</option>
                            </select>
                            <button
                              onClick={() => removeMember(member.id)}
                              className="px-2 py-1 text-xs text-red-300 hover:text-red-200 bg-red-500/20 hover:bg-red-500/30 rounded transition-colors"
                            >
                              Remove
                            </button>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'invitations' && (
            <div className="space-y-6">
              <div>
                <h3 className="font-medium text-white mb-4">Pending Invitations ({invitations.filter(i => i.status === 'pending').length})</h3>
                <div className="space-y-3">
                  {invitations.filter(i => i.status === 'pending').length === 0 ? (
                    <div className="text-center py-8 text-white/60">
                      <svg className="w-12 h-12 mx-auto mb-4 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                      </svg>
                      <p>No pending invitations</p>
                      <p className="text-sm mt-1">Send invites from the Members tab to grow your team</p>
                    </div>
                  ) : (
                    invitations.filter(i => i.status === 'pending').map((invitation) => (
                      <div key={invitation.id} className="flex items-center justify-between p-4 bg-white/5 rounded-xl">
                        <div>
                          <div className="font-medium text-white">{invitation.email}</div>
                          <div className="text-sm text-white/60">
                            Invited by {invitation.invited_by.display_name} • {new Date(invitation.created_at).toLocaleDateString()}
                          </div>
                        </div>
                        <div className="flex items-center gap-3">
                          <span className={`px-3 py-1 rounded-full text-xs font-medium ${getRoleColor(invitation.role)}`}>
                            {invitation.role.charAt(0).toUpperCase() + invitation.role.slice(1)}
                          </span>
                          <span className="px-3 py-1 rounded-full text-xs font-medium bg-yellow-500/20 text-yellow-300">
                            Pending
                          </span>
                          {canManageMembers() && (
                            <button
                              onClick={() => revokeInvitation(invitation.id)}
                              className="px-3 py-1 text-xs text-red-300 hover:text-red-200 bg-red-500/20 hover:bg-red-500/30 rounded transition-colors"
                            >
                              Revoke
                            </button>
                          )}
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>

              {/* All Invitations History */}
              {invitations.filter(i => i.status !== 'pending').length > 0 && (
                <div>
                  <h3 className="font-medium text-white mb-4">Invitation History</h3>
                  <div className="space-y-3">
                    {invitations.filter(i => i.status !== 'pending').map((invitation) => (
                      <div key={invitation.id} className="flex items-center justify-between p-4 bg-white/5 rounded-xl opacity-60">
                        <div>
                          <div className="font-medium text-white">{invitation.email}</div>
                          <div className="text-sm text-white/60">
                            Invited by {invitation.invited_by.display_name} • {new Date(invitation.created_at).toLocaleDateString()}
                          </div>
                        </div>
                        <div className="flex items-center gap-3">
                          <span className={`px-3 py-1 rounded-full text-xs font-medium ${getRoleColor(invitation.role)}`}>
                            {invitation.role.charAt(0).toUpperCase() + invitation.role.slice(1)}
                          </span>
                          <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                            invitation.status === 'accepted' ? 'bg-green-500/20 text-green-300' :
                            invitation.status === 'declined' ? 'bg-red-500/20 text-red-300' :
                            'bg-gray-500/20 text-gray-300'
                          }`}>
                            {invitation.status.charAt(0).toUpperCase() + invitation.status.slice(1)}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}