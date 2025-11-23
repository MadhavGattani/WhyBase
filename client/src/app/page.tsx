// client/src/app/page.tsx
"use client";

import { useState } from "react";
import Editor from "../components/features/Editor";
import Results from "../components/features/Results";
import Templates from "../components/features/Templates";
import Uploads from "../components/features/Uploads";
import ExportHistory from "../components/features/ExportHistory";
import History from "../components/features/History";
import { useAuth } from "../hooks/useAuth";

import { useOrganization } from "../hooks/useOrganization";
import { useToast } from "../hooks/useToast";
import { queryAI } from "../services/endpoints/queries";

export default function Page() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | undefined>(undefined);
  const [editorText, setEditorText] = useState<string>("");
  const { getToken } = useAuth();
  const { currentOrganization } = useOrganization();
  const toast = useToast();

  async function handleQuery() {
    const q = editorText.trim();
    if (!q) {
      toast.push("Enter a prompt first", "error");
      return;
    }
    setLoading(true);
    setResult(undefined);
    try {
      const token = await getToken();
      const data = await queryAI(q, {
        token,
        organizationId: currentOrganization?.id,
      });
      setResult(data.response);
    } catch (err: any) {
      setResult("Error: " + err.message);
      toast.push("Error querying AI: " + (err.message ?? ""), "error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto max-w-4xl mt-8 px-4">
      <Editor value={editorText} onChange={(v) => setEditorText(v)} onRun={handleQuery} />
      <Results loading={loading} result={result} />
      <History />
      <Templates onUse={(prompt) => setEditorText(prompt)} />
      <Uploads />
      <ExportHistory />
    </main>
  );
}