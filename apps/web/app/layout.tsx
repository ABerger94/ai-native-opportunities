import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "AI Native Opportunities",
  description: "Find and rank real AI-native jobs, contracts, freelance projects, and startup opportunities."
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
