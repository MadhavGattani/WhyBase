"use client";
import { useEffect, useRef, useState } from "react";

type EditorProps = {
  initialPrompt?: string;
  onQuery?: (q?: string) => void;
  onChange?: (text: string) => void;
};

export default function Editor({ initialPrompt = "", onQuery, onChange }: EditorProps) {
  const [text, setText] = useState<string>(initialPrompt);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  // When parent changes initialPrompt (e.g., Templates -> Use), update local state
  useEffect(() => {
    setText(initialPrompt ?? "");
  }, [initialPrompt]);

  // Inform parent when text changes
  useEffect(() => {
    if (onChange) onChange(text);
  }, [text, onChange]);

  function run() {
    if (onQuery) {
      onQuery(text);
    }
  }

  return (
    <div className="p-6">
      <textarea
        ref={textareaRef}
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Describe your task..."
        className="w-full h-44 p-4 rounded-lg bg-white/5 placeholder:text-white/50"
      />
      <div className="flex justify-between mt-4">
        <div className="text-sm text-white/60">Tip: use templates to the right to populate this box.</div>
        <div className="flex gap-2">
          <button
            onClick={() => {
              setText("");
              if (onChange) onChange("");
              textareaRef.current?.focus();
            }}
            className="px-4 py-2 rounded-lg bg-white/10 hover:bg-white/20 text-sm"
          >
            Clear
          </button>
          <button
            onClick={run}
            className="px-6 py-2 rounded-lg bg-primary hover:brightness-110"
          >
            Run
          </button>
        </div>
      </div>
    </div>
  );
}
