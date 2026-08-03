import type { Metadata } from "next";
import Link from "next/link";
import { BooklogContent } from "@/components/site/BooklogContent";

export const metadata: Metadata = {
  title: "Booklog",
  description: "2010년부터의 도서 구매 기록 아카이브.",
};

export default function BooklogPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-12 sm:max-w-4xl sm:px-6">
      <h1 className="font-[family-name:var(--font-site-serif)] text-3xl font-semibold text-[var(--site-ink)]">
        Booklog
      </h1>

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
