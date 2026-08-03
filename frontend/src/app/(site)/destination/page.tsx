import type { Metadata } from "next";
import Link from "next/link";
import { DestinationAccordion } from "@/components/site/DestinationAccordion";

export const metadata: Metadata = {
  title: "Destination",
  description: "책·영화·드라마 속 여행지 목차와 Setting Trip 지도.",
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

      <p className="mt-10 text-sm text-[var(--site-muted)]">
        <Link href="/" className="text-[var(--site-accent)] underline-offset-4 hover:underline">
          ← 홈으로
        </Link>
      </p>
    </div>
  );
}
