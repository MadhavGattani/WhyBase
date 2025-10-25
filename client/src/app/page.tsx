// client/src/app/page.tsx
"use client";

import { useState } from "react";
import Editor from "../components/Editor";
import Results from "../components/Results";
import Templates from "../components/Templates";
import Uploads from "../components/Upload";
import ExportHistory from "../components/ExportHistory";
import History from "../components/History";
import { useAuth } from "../components/AuthProvider";
import { useToast } from "../components/ToastProvider";

export default function Page() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | undefined>(undefined);
  const [editorText, setEditorText] = useState<string>("");
  const { getToken } = useAuth();
  const toast = useToast();
  const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:5000";

  async function handleQuery() {
    const q = editorText.trim();
    if (!q) {
      toast.push("Enter a prompt first", "error");
      return;
    }
    setLoading(true);
    setResult(undefined);
    try {
      const headers: any = { "Content-Type": "application/json" };
      if (getToken) {
        const token = await getToken();
        if (token) headers["Authorization"] = `Bearer ${token}`;
      }
      const res = await fetch(`${API}/api/query`, {
        method: "POST",
        headers,
        body: JSON.stringify({ prompt: q })
      });
      if (!res.ok) {
        const js = await res.json().catch(()=>({error:"Server error"}));
        throw new Error(js.error || "Query failed");
      }
      const data = await res.json();
      setResult(data.response || JSON.stringify(data));
    } catch (err: any) {
      setResult("Error: " + err.message);
      toast.push("Error querying AI: " + (err.message ?? ""), "error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto max-w-4xl mt-8 px-4">
      <Editor value={editorText} onChange={(v)=>setEditorText(v)} onRun={handleQuery} />
      <Results loading={loading} result={result} />
      <History />
      <Templates onUse={(prompt)=> setEditorText(prompt)} />
      <Uploads />
      <ExportHistory />
    </main>
  );
}
