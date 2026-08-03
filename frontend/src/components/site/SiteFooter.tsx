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
          </p>
        </div>
      </div>
    </footer>
  );
}
