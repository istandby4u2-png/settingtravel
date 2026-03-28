import Link from "next/link";
import { SITE_CONFIG } from "@/lib/site-config";

export function SiteFooter() {
  return (
    <footer className="mt-auto border-t border-[var(--site-border)] bg-[var(--site-paper)]">
      <div className="mx-auto max-w-5xl px-4 py-10 sm:px-6">
        <div className="flex flex-col gap-3 text-sm text-[var(--site-muted)]">
          <p className="text-xs">
            copyright © {SITE_CONFIG.copyright}. All rights reserved.
          </p>
          <p className="text-xs">
            <Link href="/dashboard" className="underline-offset-4 hover:text-[var(--site-ink)] hover:underline">
              관리 도구
            </Link>
            {" · "}
            <a
              href={SITE_CONFIG.legacySitesUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="underline-offset-4 hover:text-[var(--site-ink)] hover:underline"
            >
              기존 Google Sites 전체 목차
            </a>
          </p>
        </div>
      </div>
    </footer>
  );
}
