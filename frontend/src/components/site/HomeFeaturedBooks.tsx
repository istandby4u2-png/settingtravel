import Image from "next/image";
import { SITE_CONFIG } from "@/lib/site-config";

export function HomeFeaturedBooks() {
  return (
    <section className="mt-10">
      <p className="text-xs font-medium uppercase tracking-[0.35em] text-[var(--site-muted)]">
        도서
      </p>
      <ul className="mt-5 flex flex-wrap items-start justify-center gap-8 sm:gap-10">
        {SITE_CONFIG.books.map((book, i) => (
          <li key={book.href}>
            <a
              href={book.href}
              target="_blank"
              rel="noopener noreferrer"
              className="group block w-[140px] sm:w-[160px]"
            >
              <div className="overflow-hidden rounded-lg border border-[var(--site-border)] bg-white shadow-sm transition group-hover:border-[var(--site-ink)]/25 group-hover:shadow-md">
                <Image
                  src={book.coverSrc}
                  alt={`${book.label} 표지`}
                  width={320}
                  height={480}
                  priority={i === 0}
                  className="aspect-[2/3] h-auto w-full object-cover"
                  sizes="(max-width: 640px) 140px, 160px"
                />
              </div>
              <p className="mt-3 text-center text-sm font-medium leading-snug text-[var(--site-ink)] underline-offset-4 group-hover:underline">
                {book.label}
              </p>
            </a>
          </li>
        ))}
      </ul>
    </section>
  );
}
