import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/providers";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: "RepoBlueprint AI | Architectural Intelligence Engine",
  description: "Instant, evidence-based, executable architecture understanding from any repository",
  keywords: ["architecture", "code analysis", "AI", "documentation", "C4 diagrams"],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body className={`${inter.variable} font-sans antialiased text-body min-h-screen selection:bg-indigo-500/30 selection:text-indigo-200`} suppressHydrationWarning>
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  );
}
