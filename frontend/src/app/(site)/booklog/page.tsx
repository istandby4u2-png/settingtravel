import type { Metadata } from "next";
import Link from "next/link";
import { BooklogContent } from "@/components/site/BooklogContent";
import { SITE_CONFIG } from "@/lib/site-config";

export const metadata: Metadata = {
  title: "Booklog",
  description: "연도별 독서·기록.",
};

export default function BooklogPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-12 sm:max-w-4xl sm:px-6">
      <h1 className="font-[family-name:var(--font-site-serif)] text-3xl font-semibold text-[var(--site-ink)]">
        Booklog
      </h1>

      <div className="mt-6 rounded-lg border border-[var(--site-border)] bg-white/90 p-5 shadow-sm">
        <p className="text-sm font-medium text-[var(--site-ink)]">원문 Google Sites</p>
        <a
          href={SITE_CONFIG.legacySitesUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-2 inline-flex text-sm font-medium text-[var(--site-accent)] underline-offset-4 hover:underline"
        >
          전체 Booklog·목차 열기 →
        </a>
      </div>

      <div className="mt-10">
        <BooklogContent />
      </div>

      <p className="mt-12 text-sm text-[var(--site-muted)]">
        <Link href="/" className="text-[var(--site-accent)] underline-offset-4 hover:underline">
          ← 홈으로
        </Link>
      </p>
    </div>
  );
}
