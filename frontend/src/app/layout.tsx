import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

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
    <html lang="en" className={`${inter.className} h-full`}>
      <body className="min-h-full flex flex-col" style={{ backgroundColor: 'var(--color-pure-white)', color: 'var(--color-clay-black)' }}>
        {children}
      </body>
    </html>
  );
}
