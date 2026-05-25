import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Monitor Electoral - Escucha Digital",
  description: "Monitor de temáticas y sentimiento sobre elecciones en redes y medios.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
