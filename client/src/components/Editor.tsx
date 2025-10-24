"use client";
import { useState, useEffect } from "react";

export default function Editor({
  value,
  onChange,
  onRun,
}: {
  value: string;
  onChange: (v: string) => void;
  onRun: () => void;
}) {
  const [local, setLocal] = useState(value ?? "");

  useEffect(() => {
    setLocal(value ?? "");
  }, [value]);

  return (
    <div className="p-6">
      <textarea
        value={local}
        onChange={(e) => {
          setLocal(e.target.value);
          onChange(e.target.value);
        }}
        placeholder="Describe your task..."
        className="w-full h-44 p-4 rounded-lg bg-white/5 placeholder:text-white/50"
      />
      <div className="flex justify-end mt-4 gap-2">
        <button
          onClick={onRun}
          className="px-6 py-2 rounded-lg bg-primary hover:brightness-110"
        >
          Run
        </button>
      </div>
    </div>
  );
}
