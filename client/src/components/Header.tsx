// client/src/components/Header.tsx
"use client";
import AuthButton from "./AuthButton";

export default function Header() {
  return (
    <header className="w-full bg-gradient-to-r from-primary to-indigo-700 text-white p-4">
      <div className="mx-auto max-w-6xl flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-white/10 flex items-center justify-center font-bold">L</div>
          <div className="font-semibold">Loominal</div>
        </div>
        <div>
          <AuthButton />
        </div>
      </div>
    </header>
  );
}
