import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CRASHSENSE AI | Institutional-Grade Crash Analytics & Predictive Intelligence",
  description: "Advanced crash game prediction, bankroll security, and quantitative odds risk monitoring engine.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-background text-slate-100 antialiased selection:bg-brand-purple selection:text-white">
        {children}
      </body>
    </html>
  );
}

