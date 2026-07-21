import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-jetbrains-mono",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "GathaAI Studio",
  description:
    "Assistente de IA local, gratuita e inteligente. Chat com LLMs locais via Ollama.",
  keywords: ["AI", "chat", "ollama", "local", "LLM", "assistente"],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="pt-BR"
      className={`${inter.variable} ${jetbrainsMono.variable} dark h-full`}
    >
      <body className="h-full overflow-hidden">{children}</body>
    </html>
  );
}
