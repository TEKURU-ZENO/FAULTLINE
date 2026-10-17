import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "FAULTLINE | Incident Commander",
  description: "An incident commander whose entire brain lives in FalkorDB.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="antialiased bg-[#080c14] text-slate-100 min-h-screen">
        {children}
      </body>
    </html>
  );
}
