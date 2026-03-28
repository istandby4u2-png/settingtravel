"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { Menu, X } from "lucide-react";
import { SITE_CONFIG } from "@/lib/site-config";
import { cn } from "@/lib/utils";

const nav = [
  { href: "/", label: "home" },
  { href: "/destination", label: "Destination" },
  { href: "/blog", label: "Essay" },
  { href: "/genre", label: "Genre" },
  { href: "/booklog", label: "Booklog" },
  { href: "/about", label: "About" },
];

export function SiteHeader() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 border-b border-[var(--site-border)] bg-[var(--site-paper)]/95 backdrop-blur-sm">
      <div className="mx-auto flex max-w-5xl items-center gap-4 px-4 py-4 sm:px-6">
        <Link href="/" className="group min-w-0 shrink-0">
          <p className="font-[family-name:var(--font-site-serif)] text-lg font-semibold tracking-[0.12em] text-[var(--site-ink)] sm:text-xl">
            {SITE_CONFIG.title}
          </p>
          <p className="mt-0.5 truncate text-xs text-[var(--site-muted)] sm:text-sm">
            {SITE_CONFIG.tagline}
          </p>
        </Link>

        <nav className="hidden flex-1 flex-wrap items-center justify-center gap-1 md:flex">
          {nav.map((item) => {
            const active =
              item.href === "/"
                ? pathname === "/"
                : item.href === "/blog"
                  ? pathname === "/blog" || pathname.startsWith("/blog/")
                  : pathname === item.href || pathname.startsWith(`${item.href}/`);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "rounded-md px-2.5 py-1.5 text-sm transition-colors",
                  active
                    ? "bg-[var(--site-ink)] text-[var(--site-paper)]"
                    : "text-[var(--site-muted)] hover:bg-black/5 hover:text-[var(--site-ink)]"
                )}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>

        <button
          type="button"
          className="ml-auto rounded-md p-2 text-[var(--site-ink)] md:hidden"
          aria-label="Menu"
          onClick={() => setOpen((o) => !o)}
        >
          {open ? <X className="size-5" /> : <Menu className="size-5" />}
        </button>
      </div>

      {open && (
        <nav className="border-t border-[var(--site-border)] bg-[var(--site-paper)] px-4 py-3 md:hidden">
          <ul className="flex flex-col gap-1">
            {nav.map((item) => (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className="block rounded-md px-3 py-2 text-sm text-[var(--site-ink)] hover:bg-black/5"
                  onClick={() => setOpen(false)}
                >
                  {item.label}
                </Link>
              </li>
            ))}
          </ul>
        </nav>
      )}
    </header>
  );
}
