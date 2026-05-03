import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { ThemeInitializer } from "@/components/ThemeInitializer";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Yatri AI — Your AI Travel Companion",
  description: "AI-native travel planning super-app. Six specialized agents plan your perfect trip in seconds.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${inter.className} h-full`} data-theme="warm-cream">
      <body className="min-h-full flex flex-col" style={{ backgroundColor: 'var(--bg-primary)', color: 'var(--text-primary)' }}>
        <ThemeInitializer />
        {children}
      </body>
    </html>
  );
}
