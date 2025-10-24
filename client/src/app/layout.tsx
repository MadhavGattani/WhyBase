// client/src/app/layout.tsx
import "./globals.css";
import { ToastProvider } from "../components/ToastProvider";
import { AuthProvider } from "../components/AuthProvider";
import Header from "../components/Header";

export const metadata = {
  title: "Loominal",
  description: "Loominal - AI writing tool"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>
          <ToastProvider>
            <Header />
            {children}
          </ToastProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
