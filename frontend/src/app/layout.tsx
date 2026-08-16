import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "HJAI — Neural Intelligence Platform",
  description: "AI-powered autonomous agent workspace with 3D neural visualization",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
