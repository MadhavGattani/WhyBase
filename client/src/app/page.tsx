"use client";

import { useState } from "react";
import Header from "../components/Header";
import Editor from "../components/Editor";
import Results from "../components/Results";

export default function Page() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | undefined>(undefined);

  async function handleQuery(q: string) {
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
        <Editor onQuery={handleQuery} />
        <Results loading={loading} result={result} />
      </main>
    </>
  );
}
