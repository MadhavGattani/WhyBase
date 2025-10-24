"use client";
import { useEffect, useState } from "react";
import { useToast } from "./ToastProvider";

type UploadRec = { id: number; filename: string; size?: number; created_at?: string; content_type?: string };
const DEFAULT_PER_PAGE = 6;

export default function Uploads() {
  const [files, setFiles] = useState<UploadRec[]>([]);
  const [selected, setSelected] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [preview, setPreview] = useState<UploadRec | null>(null);
  const [previewText, setPreviewText] = useState<string | null>(null);
  const toast = useToast();

  useEffect(()=>{ fetchList(); }, [page]);

  async function fetchList() {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/uploads?page=${page}&per_page=${DEFAULT_PER_PAGE}`);
      if (!res.ok) throw new Error("Failed to list");
      const json = await res.json();
      setFiles(json.uploads ?? []);
      setPages(json.meta?.pages ?? 1);
    } catch (e) {
      toast.push("Failed to load uploads", "error");
    }
  }

  async function doUpload() {
    if (!selected) return toast.push("Select file", "error");
    const maxMB = Number(process.env.NEXT_PUBLIC_MAX_UPLOAD_MB || "10");
    if (selected.size > maxMB * 1024 * 1024) {
      return toast.push(`File too big. Max ${maxMB} MB allowed.`, "error");
    }
    const form = new FormData();
    form.append("file", selected);
    setLoading(true);
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/upload`, { method: "POST", body: form });
      const js = await res.json();
      if (!res.ok) throw new Error(js.error || "Upload failed");
      toast.push("Uploaded", "success");
      setSelected(null);
      fetchList();
    } catch (e: any) {
      toast.push("Error: " + e.message, "error");
    } finally {
      setLoading(false);
    }
  }

  function download(id: number) {
    const url = `${process.env.NEXT_PUBLIC_API_URL}/api/download/${id}`;
    window.open(url, "_blank");
  }

  async function openPreview(rec: UploadRec) {
    setPreview(rec);
    setPreviewText(null);
    // if text/plain or similar, fetch text
    if (rec.content_type && rec.content_type.startsWith("text")) {
      try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/download/${rec.id}`);
        const txt = await res.text();
        setPreviewText(txt);
      } catch (e) {
        setPreviewText("Unable to load preview.");
      }
    }
  }

  return (
    <section className="p-6 mt-6 border-t border-white/10">
      <h3 className="text-lg font-semibold mb-3">Upload File</h3>
      <div className="p-4 rounded bg-white/3">
        <div className="flex items-center gap-4">
          <input type="file" onChange={e=>setSelected(e.target.files?.[0]??null)} />
          <div className="flex gap-2">
            <button onClick={doUpload} disabled={!selected || loading} className="px-3 py-2 rounded bg-primary">Upload</button>
            <button onClick={()=>setSelected(null)} className="px-3 py-2 rounded bg-white/10">Clear</button>
          </div>
        </div>

        <div className="mt-4">
          <h4 className="font-medium mb-2">Uploaded Files</h4>
          {files.length === 0 && <div className="text-sm text-white/60">No files uploaded yet.</div>}
          <div className="space-y-2">
            {files.map(f => (
              <div key={f.id} className="flex items-center justify-between p-2 rounded bg-white/5">
                <div>
                  <div className="font-medium">{f.filename}</div>
                  <div className="text-xs text-white/60">{f.size ? `${f.size} bytes` : ""} {f.created_at ? ` • ${new Date(f.created_at).toLocaleString()}` : ""}</div>
                </div>
                <div className="flex gap-2">
                  <button onClick={()=>openPreview(f)} className="px-2 py-1 rounded bg-white/10 text-sm">Preview</button>
                  <button onClick={()=>download(f.id)} className="px-2 py-1 rounded bg-white/10 text-sm">Download</button>
                </div>
              </div>
            ))}
          </div>

          <div className="flex items-center justify-between mt-4">
            <div className="text-sm text-white/60">Page {page} of {pages}</div>
            <div className="flex gap-2">
              <button onClick={()=>setPage(p=>Math.max(1,p-1))} disabled={page<=1} className="px-3 py-1 rounded bg-white/10">Prev</button>
              <button onClick={()=>setPage(p=>Math.min(pages,p+1))} disabled={page>=pages} className="px-3 py-1 rounded bg-white/10">Next</button>
            </div>
          </div>
        </div>
      </div>

      {/* Preview modal */}
      {preview && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="absolute inset-0 bg-black/60" onClick={()=>{setPreview(null); setPreviewText(null);}}></div>
          <div className="relative max-w-3xl w-full mx-4 bg-surface/90 p-6 rounded-2xl">
            <div className="flex justify-between items-start gap-4">
              <h4 className="text-lg font-semibold">{preview.filename}</h4>
              <button onClick={()=>{setPreview(null); setPreviewText(null);}} className="text-sm px-2 py-1 bg-white/8 rounded">Close</button>
            </div>
            <div className="mt-4">
              {preview.content_type && preview.content_type.startsWith("text") ? (
                <pre className="whitespace-pre-wrap max-h-96 overflow-auto bg-white/3 p-3 rounded">{previewText ?? "Loading..."}</pre>
              ) : preview.content_type === "application/pdf" || preview.filename.toLowerCase().endsWith(".pdf") ? (
                <iframe src={`${process.env.NEXT_PUBLIC_API_URL}/api/download/${preview.id}`} className="w-full h-[70vh]" title="PDF preview"></iframe>
              ) : (
                <div className="text-sm">No preview available for this file type. Use Download to get the file.</div>
              )}
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
