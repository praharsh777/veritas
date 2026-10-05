import type { Metadata } from "next";
import Script from "next/script";
import "./globals.css";
import Nav from "@/components/Nav";

export const metadata: Metadata = {
  title: "VERITAS — Verify before you act",
  description: "Evidence-first verification of suspicious messages, screenshots and links.",
};

// Runs before first paint so there is no dark/light flash. Static constant; no user input.
const THEME_INIT = `(function(){try{var t=localStorage.getItem('veritas-theme');if(t!=='light'&&t!=='dark'){t=window.matchMedia('(prefers-color-scheme: light)').matches?'light':'dark'}document.documentElement.dataset.theme=t}catch(e){document.documentElement.dataset.theme='dark'}})();`;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" data-theme="dark" suppressHydrationWarning>
      <body className="min-h-screen font-sans antialiased">
        <Script id="theme-init" strategy="beforeInteractive">{THEME_INIT}</Script>
        <a href="#main" className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-lg focus:bg-brand-500 focus:px-3 focus:py-2 focus:text-ink-950">Skip to content</a>
        <Nav />
        <main id="main" className="mx-auto max-w-6xl px-5 py-8">{children}</main>
        <footer className="mx-auto max-w-6xl px-5 pb-10 text-xs text-mist-500">
          VERITAS is a safety aid, not a law-enforcement, banking, or cybersecurity authority. Submitted text is analysed on your own
          server; raw message text is not stored.
        </footer>
      </body>
    </html>
  );
}
