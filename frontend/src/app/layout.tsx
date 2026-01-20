import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/providers";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
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
    <html lang="en" className="dark">
      <body className={`${inter.variable} font-sans antialiased bg-slate-950 text-slate-50`}>
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  );
}
