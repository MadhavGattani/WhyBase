// client/src/components/Templates.tsx
"use client";
import { useEffect, useState } from "react";
import { useToast } from "../../hooks/useToast";
import { useAuth } from "../../hooks/useAuth";

type Template = { id: number; name: string; prompt: string; created_at?: string };

export default function Templates({ onUse }: { onUse: (prompt: string) => void }) {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [name, setName] = useState("");
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const toast = useToast();
  const { getToken } = useAuth();
  const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:5000";

  useEffect(() => { fetchTemplates(); }, []);

  async function fetchTemplates() {
    setLoading(true);
    try {
      const headers: any = {};
      if (getToken) {
        const token = await getToken();
        if (token) headers["Authorization"] = `Bearer ${token}`;
      }
      const res = await fetch(`${API}/api/templates`, { headers });
      const json = await res.json();
      setTemplates(json.templates ?? []);
    } catch (e) {
      toast.push("Failed to load templates", "error");
    } finally {
      setLoading(false);
    }
  }

  async function createTemplate() {
    if (!name || !prompt) return toast.push("Provide name and prompt", "error");
    try {
      const headers: any = { "Content-Type": "application/json" };
      if (getToken) {
        const token = await getToken();
        if (token) headers["Authorization"] = `Bearer ${token}`;
      }
      const res = await fetch(`${API}/api/templates`, {
        method: "POST",
        headers,
        body: JSON.stringify({ name, prompt }),
      });
      if (!res.ok) {
        const js = await res.json().catch(()=>({error:"create failed"}));
        throw new Error(js.error || "Create failed");
      }
      setName(""); setPrompt("");
      toast.push("Template saved", "success");
      fetchTemplates();
    } catch (e: any) {
      toast.push("Error: " + e.message, "error");
    }
  }

  async function removeTemplate(id: number) {
    if (!confirm("Delete template?")) return;
    try {
      const headers: any = {};
      if (getToken) {
        const token = await getToken();
        if (token) headers["Authorization"] = `Bearer ${token}`;
      }
      const res = await fetch(`${API}/api/templates/${id}`, { method: "DELETE", headers });
      if (!res.ok) throw new Error("Delete failed");
      toast.push("Template deleted", "info");
      fetchTemplates();
    } catch (e: any) {
      toast.push("Error: " + e.message, "error");
    }
  }

  async function saveEdit(t: Template, newName: string, newPrompt: string) {
    try {
      const headers: any = { "Content-Type": "application/json" };
      if (getToken) {
        const token = await getToken();
        if (token) headers["Authorization"] = `Bearer ${token}`;
      }
      const res = await fetch(`${API}/api/templates/${t.id}`, {
        method: "PUT",
        headers,
        body: JSON.stringify({ name: newName, prompt: newPrompt }),
      });
      if (!res.ok) {
        const js = await res.json().catch(()=>({error:"update failed"}));
        throw new Error(js.error || "Update failed");
      }
      toast.push("Template updated", "success");
      fetchTemplates();
    } catch (e: any) {
      toast.push("Error: " + e.message, "error");
    }
  }

  return (
    <section className="p-6 mt-6 border-t border-white/10">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white">Prompt Templates</h3>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="p-4 rounded bg-white/3">
          <h4 className="font-medium mb-2 text-white">Create Template</h4>
          <input value={name} onChange={e=>setName(e.target.value)} placeholder="Template name" className="w-full p-2 rounded bg-white/5 mb-2 text-white"/>
          <textarea value={prompt} onChange={e=>setPrompt(e.target.value)} placeholder="Prompt text" className="w-full p-2 rounded bg-white/5 h-28 text-white"/>
          <div className="flex justify-end mt-2">
            <button onClick={createTemplate} className="px-4 py-2 rounded bg-primary text-white">Save</button>
          </div>
        </div>

        <div>
          <h4 className="font-medium mb-2 text-white">Saved</h4>
          {loading ? <div className="text-white">Loading...</div> : (
            <div className="space-y-3">
              {templates.length === 0 && <div className="text-sm text-white/60">No templates</div>}
              {templates.map(t => (
                <TemplateRow key={t.id} t={t} onUse={onUse} onDelete={removeTemplate} onSave={saveEdit} />
              ))}
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

function TemplateRow({ t, onUse, onDelete, onSave }: any) {
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState(t.name);
  const [prompt, setPrompt] = useState(t.prompt);

  return (
    <div className="p-3 rounded bg-white/3 text-white">
      {!editing ? (
        <div className="flex justify-between items-start gap-2">
          <div>
            <div className="font-medium">{t.name}</div>
            <div className="text-sm text-white/70 line-clamp-3">{t.prompt}</div>
          </div>
          <div className="flex flex-col gap-2">
            <button onClick={() => onUse(t.prompt)} className="px-2 py-1 rounded bg-white/10 text-sm">Use</button>
            <button onClick={() => setEditing(true)} className="px-2 py-1 rounded bg-white/10 text-sm">Edit</button>
            <button onClick={() => onDelete(t.id)} className="px-2 py-1 rounded bg-red-600/60 text-sm">Delete</button>
          </div>
        </div>
      ) : (
        <div className="space-y-2">
          <input value={name} onChange={(e)=>setName(e.target.value)} className="w-full p-2 rounded bg-white/5 text-white" />
          <textarea value={prompt} onChange={(e)=>setPrompt(e.target.value)} className="w-full p-2 rounded bg-white/5 h-24 text-white" />
          <div className="flex justify-end gap-2">
            <button onClick={()=>{ onSave(t, name, prompt); setEditing(false); }} className="px-3 py-1 rounded bg-primary text-sm text-white">Save</button>
            <button onClick={()=>{ setName(t.name); setPrompt(t.prompt); setEditing(false); }} className="px-3 py-1 rounded bg-white/10 text-sm">Cancel</button>
          </div>
        </div>
      )}
    </div>
  );
}
