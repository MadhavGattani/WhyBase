// client/src/app/layout.tsx
import "./globals.css";
import { ToastProvider } from "../components/ToastProvider";
import { AuthProvider } from "../components/AuthProvider";
import { OrganizationProvider } from "../components/OrganizationProvider";
import Header from "../components/Header";

export const metadata = {
  title: "Loominal",
  description: "Loominal - AI writing tool with organization management"
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