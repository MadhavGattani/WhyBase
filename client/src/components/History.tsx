"use client";

import { useEffect, useState } from "react";

type Item = {
  id: number;
  prompt: string;
  response: string;
  created_at: string;
};

export default function History() {
  const [items, setItems] = useState<Item[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [perPage] = useState(6);
  const [totalPages, setTotalPages] = useState(1);
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState<Item | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    fetchHistory();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, refreshKey]);

  async function fetchHistory() {
    setLoading(true);
    setError(null);
    try {
      const q = encodeURIComponent(query);
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000"}/api/history?page=${page}&per_page=${perPage}&q=${q}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      setItems(json.history ?? []);
      setTotalPages(json.meta?.pages ?? 1);
    } catch (err: any) {
      setError(err?.message || "Failed to fetch history");
    } finally {
      setLoading(false);
    }
  }

  function refresh() {
    setPage(1);
    setRefreshKey(k => k + 1);
  }

  async function handleDelete(id: number) {
    if (!confirm("Delete this entry?")) return;
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000"}/api/history/${id}`, {
        method: "DELETE",
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      // simple refresh
      refresh();
    } catch (err: any) {
      alert("Delete failed: " + (err?.message || "unknown"));
    }
  }

  function openItem(item: Item) {
    setSelected(item);
  }
  function closeModal() {
    setSelected(null);
  }

  return (
    <section className="p-6 mt-6 border-t border-white/10">
      <div className="flex items-center justify-between mb-4 gap-4">
        <h3 className="text-lg font-semibold">History</h3>

        <div className="flex items-center gap-2">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search prompt/response"
            className="px-3 py-2 rounded bg-white/5 placeholder:text-white/60"
          />
          <button
            onClick={() => { setPage(1); fetchHistory(); }}
            className="px-3 py-2 rounded bg-white/10 hover:bg-white/20 text-sm"
          >
            Search
          </button>
          <button onClick={refresh} className="px-3 py-2 rounded bg-white/10 hover:bg-white/20 text-sm">
            Refresh
          </button>
        </div>
      </div>

      {error && <div className="text-red-400 mb-4">Error: {error}</div>}

      {loading ? (
        <div>Loading...</div>
      ) : (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {items.length === 0 && <div className="text-sm text-white/60">No history yet.</div>}
            {items.map((it) => (
              <div key={it.id} className="p-4 rounded-lg bg-white/3">
                <div className="text-xs text-white/70 mb-2">{new Date(it.created_at).toLocaleString()}</div>
                <div className="font-medium mb-2">Prompt</div>
                <pre className="whitespace-pre-wrap text-sm mb-3 line-clamp-3">{it.prompt}</pre>
                <div className="font-medium mb-1">Response</div>
                <pre className="whitespace-pre-wrap text-sm text-white/80 line-clamp-3">{it.response}</pre>

                <div className="flex justify-end gap-2 mt-3">
                  <button onClick={() => openItem(it)} className="px-3 py-1 rounded bg-white/10 hover:bg-white/20 text-sm">
                    View
                  </button>
                  <button onClick={() => handleDelete(it.id)} className="px-3 py-1 rounded bg-red-600/60 hover:brightness-90 text-sm">
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>

          {/* pagination */}
          <div className="flex items-center justify-between mt-6">
            <div className="text-sm text-white/60">
              Page {page} of {totalPages}
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page <= 1}
                className="px-3 py-1 rounded bg-white/10 hover:bg-white/20 text-sm disabled:opacity-40"
              >
                Prev
              </button>
              <button
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages}
                className="px-3 py-1 rounded bg-white/10 hover:bg-white/20 text-sm disabled:opacity-40"
              >
                Next
              </button>
            </div>
          </div>
        </>
      )}

      {/* Modal */}
      {selected && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="absolute inset-0 bg-black/60" onClick={closeModal}></div>
          <div className="relative max-w-3xl w-full mx-4 bg-surface/90 p-6 rounded-2xl">
            <div className="flex justify-between items-start gap-4">
              <h4 className="text-lg font-semibold">Entry #{selected.id}</h4>
              <button onClick={closeModal} className="text-sm px-2 py-1 bg-white/8 rounded">Close</button>
            </div>

            <div className="mt-4">
              <div className="text-xs text-white/70 mb-2">{new Date(selected.created_at).toLocaleString()}</div>

              <div className="font-medium">Prompt</div>
              <pre className="whitespace-pre-wrap bg-white/3 p-3 rounded mt-2">{selected.prompt}</pre>

              <div className="font-medium mt-4">Response</div>
              <pre className="whitespace-pre-wrap bg-white/3 p-3 rounded mt-2">{selected.response}</pre>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
