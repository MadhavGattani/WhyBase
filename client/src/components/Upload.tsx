"use client";
import { useEffect, useState } from "react";

type UploadRec = { id: number; filename: string; size?: number };

export default function Uploads() {
  const [files, setFiles] = useState<UploadRec[]>([]);
  const [selected, setSelected] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(()=>{ fetchList(); }, []);

  async function fetchList() {
    // we have no list endpoint currently; will reuse history or DB if you want.
    // For now we won't fetch list. Optionally implement server endpoint /api/uploads to list files.
  }

  async function doUpload() {
    if (!selected) return alert("Select file");
    const form = new FormData();
    form.append("file", selected);
    setLoading(true);
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/upload`, { method: "POST", body: form });
      if (!res.ok) {
        const js = await res.json().catch(()=>({error:"upload failed"}));
        throw new Error(js.error || "Upload failed");
      }
      alert("Uploaded");
      setSelected(null);
      // optional: refresh list
    } catch (e: any) {
      alert("Error: " + e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="p-6 mt-6 border-t border-white/10">
      <h3 className="text-lg font-semibold mb-3">Upload File</h3>
      <div className="p-4 rounded bg-white/3">
        <input type="file" onChange={e=>setSelected(e.target.files?.[0]??null)} />
        <div className="flex gap-2 mt-3">
          <button onClick={doUpload} disabled={!selected || loading} className="px-3 py-2 rounded bg-primary">Upload</button>
          <button onClick={()=>setSelected(null)} className="px-3 py-2 rounded bg-white/10">Clear</button>
        </div>
      </div>
    </section>
  );
}
