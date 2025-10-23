"use client";

import { useState } from "react";
import Header from "../components/Header";
import Editor from "../components/Editor";
import Results from "../components/Results";
import dynamic from "next/dynamic";

// Dynamically import History so it only runs on the client (prevents SSR issues)
const History = dynamic(() => import("../components/History"), { ssr: false });

export default function Page() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | undefined>(undefined);

  // Handles the Run button click — sends prompt to Flask backend
  async function handleQuery(q: string) {
    if (!q.trim()) return;
    setLoading(true);
    setResult(undefined);

    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000"}/api/query`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ prompt: q }),
        }
      );

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
      {/* Top header bar */}
      <Header />

      <main className="mx-auto max-w-4xl mt-8">
        {/* Input text area */}
        <Editor onQuery={handleQuery} />

        {/* Display AI response */}
        <Results loading={loading} result={result} />

        {/* Database-stored history */}
        <History />
      </main>
    </>
  );
}
