// client/src/app/layout.tsx
import "./globals.css";
import { ToastProvider } from "../components/ToastProvider";
import { AuthProvider } from "../components/AuthProvider";
<<<<<<< HEAD
import { OrganizationProvider } from "../components/OrganizationProvider";
=======
>>>>>>> d0678fe (chore: push all project files to GitHub)
import Header from "../components/Header";

export const metadata = {
  title: "Loominal",
<<<<<<< HEAD
  description: "Loominal - AI writing tool with organization management"
=======
  description: "Loominal - AI writing tool"
>>>>>>> d0678fe (chore: push all project files to GitHub)
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>
          <ToastProvider>
<<<<<<< HEAD
            <OrganizationProvider>
              <Header />
              {children}
            </OrganizationProvider>
=======
            <Header />
            {children}
>>>>>>> d0678fe (chore: push all project files to GitHub)
          </ToastProvider>
        </AuthProvider>
      </body>
    </html>
  );
}