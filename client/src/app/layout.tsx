// client/src/app/layout.tsx
import "./globals.css";
import { ToastProvider } from "../contexts/ToastContext";
import { AuthProvider } from "../contexts/AuthContext";
import { OrganizationProvider } from "../contexts/OrganizationContext";
import Header from "../components/layout/Header";

export const metadata = {
  title: "Loominal",
  description: "Loominal - AI writing tool with organization management",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>
          <ToastProvider>
            <OrganizationProvider>
              <Header />
              {children}
            </OrganizationProvider>
          </ToastProvider>
        </AuthProvider>
      </body>
    </html>
  );
}