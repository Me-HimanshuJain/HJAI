import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "HJAI Cockpit",
  description: "Advanced AI Cockpit Interface",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <head>
        <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet" />
        <link href="https://cdn.jsdelivr.net/npm/geist@1.3.0/dist/fonts/geist.css" rel="stylesheet" />
        <link href="https://cdn.jsdelivr.net/npm/geist@1.3.0/dist/fonts/geist-mono.css" rel="stylesheet" />
      </head>
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
