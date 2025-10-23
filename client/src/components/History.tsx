"use client";

import { useEffect, useState } from "react";

type Item = {
  id: number;
  prompt: string;
  response: string;
  created_at: string;
};

export default function History() {
  const [items, setItems] = useState<Item[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchHistory();
  }, []);

  async function fetchHistory() {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000"}/api/history`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      setItems(json.history ?? []);
    } catch (err: any) {
      setError(err?.message || "Failed to fetch history");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="p-6 mt-6 border-t border-white/10">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">History</h3>
        <div className="text-sm text-white/70">{loading ? "Loading..." : `${items ? items.length : 0} items`}</div>
      </div>

      {error && <div className="text-red-400 mb-4">Error: {error}</div>}

      <div className="space-y-4">
        {items && items.length === 0 && <div className="text-sm text-white/60">No history yet.</div>}
        {items?.map((it) => (
          <div key={it.id} className="p-4 rounded-lg bg-white/3">
            <div className="text-xs text-white/70 mb-2">{new Date(it.created_at).toLocaleString()}</div>
            <div className="font-medium mb-2">Prompt</div>
            <pre className="whitespace-pre-wrap text-sm mb-3">{it.prompt}</pre>
            <div className="font-medium mb-1">Response</div>
            <pre className="whitespace-pre-wrap text-sm text-white/80">{it.response}</pre>
          </div>
        ))}
      </div>

      <div className="flex justify-end mt-4">
        <button
          onClick={fetchHistory}
          className="px-4 py-2 rounded bg-white/10 hover:bg-white/20 text-sm"
        >
          Refresh
        </button>
      </div>
    </section>
  );
}
