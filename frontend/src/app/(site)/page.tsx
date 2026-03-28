import { HomeFeaturedBooks } from "@/components/site/HomeFeaturedBooks";
import { HomeLatestEssays } from "@/components/site/HomeLatestEssays";
import { SITE_CONFIG } from "@/lib/site-config";

export default function HomePage() {
  return (
    <div className="pb-16 pt-10 sm:pb-24 sm:pt-14">
      <section className="mx-auto max-w-5xl px-4 text-center sm:px-6">
        <p className="text-xs font-medium uppercase tracking-[0.35em] text-[var(--site-muted)]">
          Destination
        </p>
        <h1 className="mt-4 font-[family-name:var(--font-site-serif)] text-4xl font-semibold tracking-tight text-[var(--site-ink)] sm:text-5xl">
          {SITE_CONFIG.title}
        </h1>
        <p className="mx-auto mt-4 max-w-2xl text-lg text-[var(--site-muted)] leading-relaxed">
          {SITE_CONFIG.tagline}
        </p>
        <div className="mt-8 flex flex-wrap items-center justify-center gap-3 text-sm">
          <a
            href={SITE_CONFIG.brunch}
            target="_blank"
            rel="noopener noreferrer"
            className="rounded-full border border-[var(--site-border)] bg-white px-4 py-2 text-[var(--site-ink)] shadow-sm transition hover:border-[var(--site-ink)]/20"
          >
            Brunch
          </a>
          <a
            href={SITE_CONFIG.naverBlog}
            target="_blank"
            rel="noopener noreferrer"
            className="rounded-full border border-[var(--site-border)] bg-white px-4 py-2 text-[var(--site-ink)] shadow-sm transition hover:border-[var(--site-ink)]/20"
          >
            Naver Blog
          </a>
          <a
            href={SITE_CONFIG.social.instagram}
            target="_blank"
            rel="noopener noreferrer"
            className="rounded-full border border-[var(--site-border)] bg-white px-4 py-2 text-[var(--site-ink)] shadow-sm transition hover:border-[var(--site-ink)]/20"
          >
            Instagram
          </a>
          <a
            href={SITE_CONFIG.social.youtube}
            target="_blank"
            rel="noopener noreferrer"
            className="rounded-full border border-[var(--site-border)] bg-white px-4 py-2 text-[var(--site-ink)] shadow-sm transition hover:border-[var(--site-ink)]/20"
          >
            YouTube
          </a>
        </div>

        <HomeFeaturedBooks />
      </section>

      <div className="mx-auto mt-16 max-w-5xl border-t border-[var(--site-border)] px-4 sm:px-6" />

      <div className="mt-16">
        <HomeLatestEssays />
      </div>
    </div>
  );
}
