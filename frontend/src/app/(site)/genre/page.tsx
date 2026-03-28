import type { Metadata } from "next";
import Link from "next/link";
import { SITE_CONFIG } from "@/lib/site-config";

export const metadata: Metadata = {
  title: "Genre",
  description: "book · drama · movie 등 장르별 기록.",
};

export default function GenrePage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-12 sm:px-6">
      <h1 className="font-[family-name:var(--font-site-serif)] text-3xl font-semibold text-[var(--site-ink)]">
        Genre
      </h1>
      <p className="mt-4 text-[var(--site-muted)] leading-relaxed">
        도서, 드라마, 영화 등 <strong>장르별로 정리된 긴 목록</strong>은 현재 Google Sites에 있습니다. 이
        프로젝트에서는 에세이·분석 도구를 중심으로 옮기고, 나머지는 원문으로 연결합니다.
      </p>
      <a
        href={SITE_CONFIG.legacySitesUrl}
        target="_blank"
        rel="noopener noreferrer"
        className="mt-8 inline-flex rounded-md bg-[var(--site-ink)] px-4 py-2.5 text-sm font-medium text-white hover:opacity-90"
      >
        Genre 전체 (Google Sites)
      </a>
      <p className="mt-8 text-sm text-[var(--site-muted)]">
        <Link href="/" className="text-[var(--site-accent)] underline-offset-4 hover:underline">
          ← 홈으로
        </Link>
      </p>
    </div>
  );
}
