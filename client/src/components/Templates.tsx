"use client";
import { useEffect, useState } from "react";

type Template = { id: number; name: string; prompt: string; created_at?: string };

export default function Templates({ onUse }: { onUse: (prompt: string) => void }) {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [name, setName] = useState("");
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => { fetchTemplates(); }, []);

  async function fetchTemplates() {
    setLoading(true);
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/templates`);
      const json = await res.json();
      setTemplates(json.templates ?? []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  async function createTemplate() {
    if (!name || !prompt) return alert("Provide name and prompt");
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/templates`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, prompt }),
      });
      if (!res.ok) throw new Error("Create failed");
      setName(""); setPrompt("");
      fetchTemplates();
    } catch (e: any) {
      alert("Error: " + e.message);
    }
  }

  async function removeTemplate(id: number) {
    if (!confirm("Delete template?")) return;
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/templates/${id}`, { method: "DELETE" });
      if (!res.ok) throw new Error("Delete failed");
      fetchTemplates();
    } catch (e: any) {
      alert("Error: " + e.message);
    }
  }

  return (
    <section className="p-6 mt-6 border-t border-white/10">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Prompt Templates</h3>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="p-4 rounded bg-white/3">
          <h4 className="font-medium mb-2">Create Template</h4>
          <input value={name} onChange={e=>setName(e.target.value)} placeholder="Template name" className="w-full p-2 rounded bg-white/5 mb-2"/>
          <textarea value={prompt} onChange={e=>setPrompt(e.target.value)} placeholder="Prompt text" className="w-full p-2 rounded bg-white/5 h-28"/>
          <div className="flex justify-end mt-2">
            <button onClick={createTemplate} className="px-4 py-2 rounded bg-primary">Save</button>
          </div>
        </div>

        <div>
          <h4 className="font-medium mb-2">Saved</h4>
          {loading ? <div>Loading...</div> : (
            <div className="space-y-3">
              {templates.length === 0 && <div className="text-sm text-white/60">No templates</div>}
              {templates.map(t => (
                <div key={t.id} className="p-3 rounded bg-white/3">
                  <div className="flex justify-between items-start gap-2">
                    <div>
                      <div className="font-medium">{t.name}</div>
                      <div className="text-sm text-white/70 line-clamp-3">{t.prompt}</div>
                    </div>
                    <div className="flex flex-col gap-2">
                      <button onClick={()=>onUse(t.prompt)} className="px-2 py-1 rounded bg-white/10 text-sm">Use</button>
                      <button onClick={()=>removeTemplate(t.id)} className="px-2 py-1 rounded bg-red-600/60 text-sm">Delete</button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
