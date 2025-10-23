"use client";

export default function ExportHistory() {
  async function download(format: "csv" | "json") {
    const url = `${process.env.NEXT_PUBLIC_API_URL}/api/export?format=${format}`;
    // navigate to the URL to download
    window.open(url, "_blank");
  }

  return (
    <div className="p-6 mt-4">
      <h4 className="font-medium mb-2">Export</h4>
      <div className="flex gap-2">
        <button onClick={()=>download("csv")} className="px-3 py-2 rounded bg-white/10">Download CSV</button>
        <button onClick={()=>download("json")} className="px-3 py-2 rounded bg-white/10">Download JSON</button>
      </div>
    </div>
  );
}
