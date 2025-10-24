"use client";

import { useState } from "react";
import Header from "../components/Header";
import Editor from "../components/Editor";
import Results from "../components/Results";
import dynamic from "next/dynamic";
import Templates from "../components/Templates";
import Uploads from "../components/Upload";
import ExportHistory from "../components/ExportHistory";

const History = dynamic(() => import("../components/History"), { ssr: false });

export default function Page() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | undefined>(undefined);

  // LIFTED editor text state
  const [editorText, setEditorText] = useState<string>("");

  async function handleQuery() {
    const q = editorText.trim();
    if (!q) {
      alert("Please enter a prompt");
      return;
    }
    setLoading(true);
    setResult(undefined);
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000'}/api/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: q }),
      });
      const data = await res.json();
      setResult(data.response || JSON.stringify(data));
    } catch (err: any) {
      setResult("Error: " + err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <Header />
      <main className="mx-auto max-w-4xl mt-8">
        <Editor value={editorText} onChange={(v)=>setEditorText(v)} onRun={handleQuery} />
        <Results loading={loading} result={result} />
        <History />
        <Templates onUse={(prompt)=> setEditorText(prompt)} />
        <Uploads />
        <ExportHistory />
      </main>
    </>
  );
}
