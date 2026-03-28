import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "about this site...",
  description:
    "배경여행이란, 사이트의 규정, 콘텐츠 이용 안내 — www.istandby4u2.com 원문과 동일합니다.",
};

export default function AboutPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-12 sm:px-6">
      <h1 className="font-[family-name:var(--font-site-serif)] text-3xl font-semibold text-[var(--site-ink)]">
        about this site...
      </h1>

      <article className="mt-10 space-y-8 text-[var(--site-ink)] leading-relaxed">
        <section className="space-y-4">
          <h2 className="font-[family-name:var(--font-site-serif)] text-xl font-semibold">
            배경여행이란?
          </h2>
          <p className="text-[var(--site-muted)]">
            책, 영화, 드라마 속 인물들이 다녀간 장소를 가보고, 묘사된 요리도 맛보는 여행입니다.
          </p>
          <p className="text-[var(--site-muted)]">
            책, 영화, 드라마를 보고 느낀 마음의 여운을 다시 한 번 느껴보시길 바랍니다.
          </p>
        </section>

        <section className="space-y-4">
          <h2 className="font-[family-name:var(--font-site-serif)] text-xl font-semibold">
            사이트의 규정
          </h2>
          <p className="text-[var(--site-muted)]">
            직접 찍은 사진, 직접 작성한 글로 구성했습니다.
          </p>
          <p className="text-[var(--site-muted)]">
            책표지, 영화 팜플렛 등은 링크를 이용하여 게재하였습니다.
          </p>
        </section>

        <section className="space-y-4">
          <h2 className="font-[family-name:var(--font-site-serif)] text-xl font-semibold">
            컨텐츠의 이용
          </h2>
          <p className="text-[var(--site-muted)]">
            해당 사이트의 모든 콘텐츠는 상업적 용도가 아닌 경우에 한하여, 링크를 통해 사용이 가능합니다.
          </p>
          <p className="text-[var(--site-muted)]">
            온오프라인에 게재를 원하실 경우, 반드시 출전을 밝혀주시길 바랍니다.
          </p>
          <p className="text-sm text-[var(--site-muted)]">
            저작권명: ⓒ istandby4u2
            <br />
            소유자: moonee lee (istandby4u2@naver.com)
            <br />
            출처:{" "}
            <a
              href="https://www.istandby4u2.com/"
              target="_blank"
              rel="noopener noreferrer"
              className="font-medium text-[var(--site-accent)] underline-offset-4 hover:underline"
            >
              www.istandby4u2.com
            </a>
          </p>
          <p className="text-[var(--site-muted)]">
            그밖에 개인적으로 여행 시 참고하시거나, 인용하시는 것은 언제든 가능합니다.
          </p>
          <p className="text-[var(--site-muted)]">
            사이트와 관련된 모든 문의사항은 하단에 댓글을 남겨주시거나 메일(
            <a
              href="mailto:istandby4u2@naver.com"
              className="text-[var(--site-accent)] underline-offset-4 hover:underline"
            >
              istandby4u2@naver.com
            </a>
            )을 보내주시길 바랍니다.
          </p>
          <p className="text-[var(--site-muted)]">감사합니다.</p>
        </section>
      </article>

      <p className="mt-12 text-sm text-[var(--site-muted)]">
        <Link href="/" className="text-[var(--site-accent)] underline-offset-4 hover:underline">
          ← 홈으로
        </Link>
      </p>
    </div>
  );
}
