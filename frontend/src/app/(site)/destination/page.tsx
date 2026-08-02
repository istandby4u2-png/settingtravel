import type { Metadata } from "next";
import Link from "next/link";
import { DestinationAccordion } from "@/components/site/DestinationAccordion";
import { SITE_CONFIG } from "@/lib/site-config";

export const metadata: Metadata = {
  title: "Destination",
  description: "책·영화·드라마 속 여행지 목차. 기존 Google Sites와 연결됩니다.",
};

export default function DestinationPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-12 sm:max-w-4xl sm:px-6">
      <h1 className="font-[family-name:var(--font-site-serif)] text-3xl font-semibold text-[var(--site-ink)]">
        Destination
      </h1>
      {/* Google My Maps 세계 여행지 지도 */}
      <div className="mt-8">
        <div className="overflow-hidden rounded-lg border border-[var(--site-border)] shadow-sm">
          <iframe
            src="https://www.google.com/maps/d/embed?mid=12mTMIslQaT_Gzt1TBJfSF8QWIgFfCsRv&ll=29.95857899570913,87.96888877187494&z=2"
            width="100%"
            height="480"
            style={{ border: 0, display: "block" }}
            allowFullScreen
            loading="lazy"
            referrerPolicy="no-referrer-when-downgrade"
            title="배경여행 세계 여행지 지도"
          />
        </div>
      </div>

      <p className="mt-10 text-sm text-[var(--site-muted)]">
        항목을 눌러 펼치거나 접습니다. 데이터 파일:{" "}
        <code className="rounded bg-black/5 px-1.5 py-0.5 text-xs">src/data/destination-tree.json</code>
      </p>

      <div className="mt-6">
        <DestinationAccordion />
      </div>

      <p className="mt-10 text-[var(--site-muted)] leading-relaxed">
        아래 목차는 기존 Google Sites의 <strong>일부</strong>를 JSON으로 옮겨 온 것입니다. 전체 페이지·최신
        수정은{" "}
        <a
          href={SITE_CONFIG.legacySitesUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="font-medium text-[var(--site-accent)] underline-offset-4 hover:underline"
        >
          Google Sites
        </a>
        에서 확인할 수 있습니다.
      </p>

      <div className="mt-6 rounded-lg border border-[var(--site-border)] bg-white/90 p-5 shadow-sm sm:p-6">
        <p className="text-sm font-medium text-[var(--site-ink)]">기존 사이트에서 전체 보기</p>
        <a
          href={SITE_CONFIG.legacySitesUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-3 inline-flex rounded-md bg-[var(--site-ink)] px-4 py-2.5 text-sm font-medium text-white hover:opacity-90"
        >
          istandby4u2 (Google Sites) 열기
        </a>
      </div>

      <p className="mt-10 text-sm text-[var(--site-muted)]">
        <Link href="/" className="text-[var(--site-accent)] underline-offset-4 hover:underline">
          ← 홈으로
        </Link>
      </p>
    </div>
  );
}
