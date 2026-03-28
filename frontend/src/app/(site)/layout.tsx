import type { Metadata } from "next";
import { Noto_Sans_KR, Noto_Serif_KR } from "next/font/google";
import { SiteHeader } from "@/components/site/SiteHeader";
import { SiteFooter } from "@/components/site/SiteFooter";
import { SITE_CONFIG } from "@/lib/site-config";

const siteSans = Noto_Sans_KR({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-site-sans",
  display: "swap",
});

const siteSerif = Noto_Serif_KR({
  subsets: ["latin"],
  weight: ["500", "600", "700"],
  variable: "--font-site-serif",
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: `${SITE_CONFIG.title} — ${SITE_CONFIG.tagline}`,
    template: `%s | ${SITE_CONFIG.title}`,
  },
  description:
    "책·영화·드라마 속 여행지와 이야기. 에세이·여행 기록·장르·북로그.",
};

export default function SiteLayout({ children }: { children: React.ReactNode }) {
  return (
    <div
      className={`${siteSans.variable} ${siteSerif.variable} flex min-h-screen flex-col bg-[var(--site-paper)] font-[family-name:var(--font-site-sans)] text-[var(--site-ink)] antialiased`}
    >
      <SiteHeader />
      <main className="flex-1">{children}</main>
      <SiteFooter />
    </div>
  );
}
