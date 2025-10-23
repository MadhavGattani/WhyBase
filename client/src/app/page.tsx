"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import Header from "../components/Header";
import Editor from "../components/Editor";
import Results from "../components/Results";
import Templates from "../components/Templates";
import Uploads from "../components/Upload";
import ExportHistory from "../components/ExportHistory";

const History = dynamic(() => import("../components/History"), { ssr: false });

export default function Page() {
  // Editor text is lifted to the page so Templates can set it
  const [editorText, setEditorText] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | undefined>(undefined);

  // Called by Editor when user clicks Run (or parent can call directly)
  async function handleQuery(prompt?: string) {
    const q = (prompt ?? editorText ?? "").trim();
    if (!q) {
      setResult("Please enter a prompt.");
      return;
    }

    setLoading(true);
    setResult(undefined);
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000"}/api/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: q }),
      });
      const data = await res.json();
      setResult(data.response || JSON.stringify(data));
    } catch (err: any) {
      setResult("Error: " + (err?.message ?? String(err)));
    } finally {
      setLoading(false);
    }
  }

  // Templates `Use` button calls this to populate the editor
  function handleUseTemplate(promptText: string) {
    setEditorText(promptText);
    // Optionally auto-run after inserting:
    // handleQuery(promptText);
  }

  return (
    <>
      <Header />
      <main className="mx-auto max-w-4xl mt-8">
        <Editor
          initialPrompt={editorText}
          onChange={(txt) => setEditorText(txt)}
          onQuery={() => handleQuery()} // Editor will call this when Run pressed
        />

        <Results loading={loading} result={result} />

        {/* History (client only) */}
        <History />

        {/* Templates: pass handler so "Use" populates the editor */}
        <Templates onUse={handleUseTemplate} />

        {/* Upload UI */}
        <Uploads />

        {/* Export buttons */}
        <ExportHistory />
      </main>
    </>
  );
}
