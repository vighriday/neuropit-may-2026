import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "NeuroPit Cognitive Twin OS",
  description:
    "Real time Cognitive Twin Operating System for motorsport. Telemetry is infrastructure. Cognition is the product. Built by Hriday Vig for the IBM AI Builders Challenge 2026 powered by IBM SkillsBuild.",
  applicationName: "NeuroPit Cognitive Twin OS",
  authors: [{ name: "Hriday Vig", url: "https://github.com/vighriday" }],
  creator: "Hriday Vig",
  publisher: "Hriday Vig",
  keywords: [
    "NeuroPit",
    "Cognitive Twin Operating System",
    "motorsport",
    "Formula 1",
    "IBM Granite",
    "IBM Docling",
    "Langflow",
    "IBM SkillsBuild",
    "AI Builders Challenge",
    "Hriday Vig",
  ],
  icons: {
    icon: "/neuropit-logo.png",
    shortcut: "/neuropit-logo.png",
    apple: "/neuropit-logo.png",
  },
  openGraph: {
    title: "NeuroPit Cognitive Twin OS",
    description:
      "Real time Cognitive Twin Operating System for motorsport. Built by Hriday Vig for the IBM AI Builders Challenge 2026.",
    images: ["/neuropit-logo.png"],
    siteName: "NeuroPit",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>{children}</body>
    </html>
  );
}
