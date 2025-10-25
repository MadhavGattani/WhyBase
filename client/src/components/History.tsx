// client/src/components/History.tsx
"use client";
import { useEffect, useState } from "react";

type QueryItem = { id: number; prompt: string; response: string; created_at?: string };

export default function History() {
  const [items, setItems] = useState<QueryItem[]>([]);
  const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:5000";

  useEffect(() => {
    (async () => {
      try {
        const res = await fetch(`${API}/api/queries`);
        if (!res.ok) return;
        const js = await res.json();
        setItems(js.queries ?? []);
      } catch (e) {
        // ignore
      }
    })();
  }, []);

  if (items.length === 0) return null;

  return (
    <section className="mt-6 p-4 rounded bg-white/3 text-white">
      <h4 className="font-medium mb-2">Recent History</h4>
      <div className="space-y-3">
        {items.map(it => (
          <div key={it.id} className="p-3 rounded bg-white/5">
            <div className="text-sm text-white/80">{it.prompt}</div>
            <div className="text-xs text-white/60 mt-1">{it.response?.slice(0, 200)}</div>
            <div className="text-xs text-white/40 mt-2">{it.created_at ? new Date(it.created_at).toLocaleString() : ""}</div>
          </div>
        ))}
      </div>
    </section>
  );
}