"use client";
import { useState } from "react";

export default function Editor({ onQuery }: { onQuery: (q: string) => void }) {
  const [text, setText] = useState("");

  return (
    <div className="p-6">
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Describe your task..."
        className="w-full h-44 p-4 rounded-lg bg-white/5 placeholder:text-white/50"
      />
      <div className="flex justify-end mt-4">
        <button
          onClick={() => { onQuery(text); }}
          className="px-6 py-2 rounded-lg bg-primary hover:brightness-110"
        >
          Run
        </button>
      </div>
    </div>
  );
}
