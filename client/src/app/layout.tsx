// client/src/app/layout.tsx
import "./globals.css"; // your Tailwind + global styles
import { ReactNode } from "react";
import { ToastProvider } from "../components/ToastProvider";
import Header from "../components/Header"; // optional; remove if you don't have Header

export const metadata = {
  title: "Loominal — Local Dev",
  description: "Loominal clone - development build",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <head />
      <body className="bg-gradient-to-b from-surface/80 to-black text-white min-h-screen">
        <ToastProvider>
          {/* Optional header — keep the same Header component if present */}
          {typeof Header !== "undefined" ? <Header /> : null}

          <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
            {children}
          </div>
        </ToastProvider>
      </body>
    </html>
  );
}
