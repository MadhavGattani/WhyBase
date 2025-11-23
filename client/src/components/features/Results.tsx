// client/src/components/Results.tsx
"use client";

export default function Results({ loading, result }: { loading: boolean; result?: string | undefined }) {
  return (
    <div className="mt-6 p-6 bg-white/3 rounded-lg text-white">
      <h3 className="text-lg font-medium mb-3">Output</h3>
      {loading ? <div>Loading…</div> : (
        <pre className="whitespace-pre-wrap">{result ?? "No output yet — run a prompt."}</pre>
      )}
    </div>
  );
}
