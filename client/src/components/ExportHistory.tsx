// client/src/components/ExportHistory.tsx
"use client";
import { useToast } from "./ToastProvider";
import { useAuth } from "./AuthProvider";

export default function ExportHistory() {
  const toast = useToast();
  const { getToken } = useAuth();
  const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:5000";

  async function exportCsv() {
    try {
      const headers: any = {};
      if (getToken) {
        const token = await getToken();
        if (token) headers["Authorization"] = `Bearer ${token}`;
      }
      const res = await fetch(`${API}/api/export?format=csv`, { headers });
      if (!res.ok) throw new Error("Export failed");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "loominal_history.csv";
      a.click();
      URL.revokeObjectURL(url);
      toast.push("Export started", "success");
    } catch (e: any) {
      toast.push("Export failed: " + e.message, "error");
    }
  }

  async function exportJson() {
    try {
      const headers: any = {};
      if (getToken) {
        const token = await getToken();
        if (token) headers["Authorization"] = `Bearer ${token}`;
      }
      const res = await fetch(`${API}/api/export?format=json`, { headers });
      if (!res.ok) throw new Error("Export failed");
      const js = await res.json();
      const blob = new Blob([JSON.stringify(js, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "loominal_history.json";
      a.click();
      URL.revokeObjectURL(url);
      toast.push("Export started", "success");
    } catch (e: any) {
      toast.push("Export failed: " + e.message, "error");
    }
  }

  return (
    <section className="mt-6 p-4 bg-white/3 rounded text-white">
      <h4 className="font-medium mb-2">Export</h4>
      <div className="flex gap-2">
        <button onClick={exportCsv} className="px-3 py-2 rounded bg-primary">Export CSV</button>
        <button onClick={exportJson} className="px-3 py-2 rounded bg-white/10">Export JSON</button>
      </div>
    </section>
  );
}
