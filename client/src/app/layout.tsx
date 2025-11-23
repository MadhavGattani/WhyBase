// client/src/app/layout.tsx
import "./globals.css";
import { ToastProvider } from "../contexts/ToastContext";
import { AuthProvider } from "../contexts/AuthContext";
import { OrganizationProvider } from "../contexts/OrganizationContext";
import Header from "../components/layout/Header";
import ErrorBoundary from "../components/common/ErrorBoundary";  // ✅ Added

export const metadata = {
  title: "Loominal",
  description: "Loominal - AI writing tool with organization management",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <ErrorBoundary>  {/* ✅ Wrapped everything */}
          <AuthProvider>
            <ToastProvider>
              <OrganizationProvider>
                <Header />
                {children}
              </OrganizationProvider>
            </ToastProvider>
          </AuthProvider>
        </ErrorBoundary>
      </body>
    </html>
  );
}