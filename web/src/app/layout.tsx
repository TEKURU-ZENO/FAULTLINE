import type { Metadata, Viewport } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const sans = Geist({ subsets: ["latin"], variable: "--font-sans", display: "swap" });
const mono = Geist_Mono({ subsets: ["latin"], variable: "--font-mono", display: "swap" });

export const metadata: Metadata = {
  title: "FAULTLINE — Incident commander",
  description: "A multi-agent incident commander whose whole brain lives in FalkorDB.",
  openGraph: {
    title: "FAULTLINE",
    description: "A multi-agent incident commander whose whole brain lives in FalkorDB.",
  },
};

export const viewport: Viewport = {
  themeColor: "#0a0c0f",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`dark ${sans.variable} ${mono.variable}`}>
      <body className="grain antialiased bg-ink-950 text-ink-100 min-h-dvh">
        <a
          href="#topology"
          className="sr-only focus:not-sr-only focus:fixed focus:left-3 focus:top-3 focus:z-modal focus:rounded-md focus:bg-ink-800 focus:px-3 focus:py-2 focus:text-sm"
        >
          Skip to topology
        </a>
        {children}
      </body>
    </html>
  );
}
