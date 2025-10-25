// client/src/components/ToastProvider.tsx
"use client";
import React, { createContext, useContext, useState, ReactNode } from "react";

type Toast = { id: number; msg: string; type?: "info" | "success" | "error"; ttl?: number };
type ToastCtx = { push: (msg: string, type?: Toast["type"], ttl?: number) => void };

const ToastContext = createContext<ToastCtx | null>(null);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  function push(msg: string, type: Toast["type"] = "info", ttl = 4000) {
    const id = Date.now() + Math.floor(Math.random() * 1000);
    const t: Toast = { id, msg, type, ttl };
    setToasts((s) => [t, ...s]);
    setTimeout(() => {
      setToasts((s) => s.filter((x) => x.id !== id));
    }, ttl);
  }

  return (
    <ToastContext.Provider value={{ push }}>
      {children}
      <div style={{ position: "fixed", right: 16, top: 16, zIndex: 9999, display: "flex", flexDirection: "column", gap: 8 }}>
        {toasts.map((t) => (
          <div key={t.id} style={{
            padding: "10px 14px",
            borderRadius: 8,
            background: t.type === "error" ? "rgba(220,38,38,0.9)" : t.type === "success" ? "rgba(16,185,129,0.9)" : "rgba(255,255,255,0.12)",
            color: "white",
            boxShadow: "0 6px 18px rgba(0,0,0,0.4)",
            maxWidth: 360,
            fontSize: 13
          }}>
            {t.msg}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used inside ToastProvider");
  return ctx;
}
