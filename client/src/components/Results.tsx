export default function Results({ loading, result }: { loading: boolean, result?: string }) {
  return (
    <div className="p-6">
      <h2 className="text-sm text-white/80 mb-2">Output</h2>
      <div className="min-h-[160px] p-4 rounded-lg bg-white/3">
        {loading ? <div>Loading...</div> : <pre className="whitespace-pre-wrap">{result}</pre>}
      </div>
    </div>
  );
}
