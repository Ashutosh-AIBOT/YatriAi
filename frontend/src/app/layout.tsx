import type { Metadata } from "next";
import "./globals.css";
import { ThemeInitializer } from "@/components/ThemeInitializer";

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
    <html lang="en" className="h-full" data-theme="warm-cream">
      <body className="min-h-full flex flex-col" style={{ backgroundColor: 'var(--bg-primary)', color: 'var(--text-primary)' }}>
        <ThemeInitializer />
        {children}
      </body>
    </html>
  );
}
