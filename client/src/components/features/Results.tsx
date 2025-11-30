// REPLACE client/src/components/features/Results.tsx with this

"use client";

interface Source {
  type: string;
  title: string;
  url: string;
  metadata?: {
    repository?: string;
    state?: string;
    language?: string;
    stars?: number;
  };
}

interface ResultsProps {
  loading: boolean;
  result?: string;
  sources?: Source[];
  contextUsed?: boolean;
}

export default function Results({ loading, result, sources, contextUsed }: ResultsProps) {
  const getSourceIcon = (type: string) => {
    if (type === "issue") {
      return (
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      );
    }
    return (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
      </svg>
    );
  };

  const getSourceColor = (type: string) => {
    if (type === "issue") return "border-blue-500/30 bg-blue-500/10";
    return "border-purple-500/30 bg-purple-500/10";
  };

  return (
    <div className="mt-6">
      {/* Main Response */}
      <div className="p-6 bg-white/3 rounded-lg text-white">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-medium">Output</h3>
          {contextUsed && (
            <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-green-500/20 text-green-300 text-xs">
              <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              Context-Enhanced
            </div>
          )}
        </div>
        
        {loading ? (
          <div className="flex items-center gap-3 text-white/60">
            <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
            <span>Generating response...</span>
          </div>
        ) : (
          <pre className="whitespace-pre-wrap text-white/90 leading-relaxed">
            {result ?? "No output yet — run a prompt."}
          </pre>
        )}
      </div>

      {/* Sources/Citations */}
      {sources && sources.length > 0 && (
        <div className="mt-4 p-5 bg-white/5 rounded-lg border border-white/10">
          <div className="flex items-center gap-2 mb-4">
            <svg className="w-5 h-5 text-white/70" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
            </svg>
            <h4 className="font-medium text-white">Sources Referenced ({sources.length})</h4>
          </div>
          
          <div className="space-y-2">
            {sources.map((source, index) => (
              <a
                key={index}
                href={source.url}
                target="_blank"
                rel="noopener noreferrer"
                className={`
                  block p-3 rounded-lg border transition-all duration-200
                  ${getSourceColor(source.type)}
                  hover:bg-white/10 hover:border-white/20
                  group
                `}
              >
                <div className="flex items-start gap-3">
                  <div className="mt-0.5 text-white/60 group-hover:text-white/80 transition-colors">
                    {getSourceIcon(source.type)}
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-white/90 group-hover:text-white transition-colors truncate">
                      {source.title}
                    </div>
                    
                    {source.metadata && (
                      <div className="flex items-center gap-3 mt-1 text-xs text-white/50">
                        {source.metadata.repository && (
                          <span className="flex items-center gap-1">
                            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                            </svg>
                            {source.metadata.repository}
                          </span>
                        )}
                        {source.metadata.state && (
                          <span className={`px-2 py-0.5 rounded ${
                            source.metadata.state === 'open' ? 'bg-green-500/20 text-green-300' : 'bg-purple-500/20 text-purple-300'
                          }`}>
                            {source.metadata.state}
                          </span>
                        )}
                        {source.metadata.language && (
                          <span className="flex items-center gap-1">
                            <span className="w-2 h-2 rounded-full bg-blue-400" />
                            {source.metadata.language}
                          </span>
                        )}
                        {source.metadata.stars !== undefined && (
                          <span>⭐ {source.metadata.stars}</span>
                        )}
                      </div>
                    )}
                  </div>
                  
                  <svg 
                    className="w-4 h-4 text-white/40 group-hover:text-white/60 transition-colors flex-shrink-0 mt-1" 
                    fill="none" 
                    viewBox="0 0 24 24" 
                    stroke="currentColor"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                  </svg>
                </div>
              </a>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}