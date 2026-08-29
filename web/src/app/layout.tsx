import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Clause Lens — Contract Intelligence",
  description:
    "Query your contracts in natural language. Powered by retrieval-augmented AI with a live context inspector.",
  keywords: ["contract analysis", "legal AI", "clause search", "MCP"],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </head>
      <body>{children}</body>
    </html>
  );
}
