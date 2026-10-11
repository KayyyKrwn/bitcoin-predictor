import type { Metadata } from "next";
import "./globals.css";
import Navbar from "@/components/Navbar";

export const metadata: Metadata = {
  title: "Bitcoin Predictor | N-BEATS",
  description:
    "Prediksi harga Bitcoin (BTC-USD) dengan model N-BEATS — project portofolio dari hasil skripsi.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="id" className="dark">
      <body className="min-h-screen antialiased">
        <Navbar />
        <main className="mx-auto max-w-6xl px-4 pt-8">{children}</main>
        <footer className="mx-auto max-w-6xl px-4 py-10 text-center text-xs text-white/40">
          Bitcoin Predictor · N-BEATS + Adam · Data realtime Yahoo Finance ·
          Project portofolio/edukasi, bukan saran investasi.
        </footer>
      </body>
    </html>
  );
}
