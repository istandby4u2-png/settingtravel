"use client";

import { useCallback, useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { api, type BooklogItem } from "@/lib/api";

const PAGE_SIZE = 100;

type Filter = number | "all" | "unassigned";

const SOURCE_LABEL: Record<string, string> = {
  backdata: "배경여행 DB",
  google_sites: "Google Sites",
  kyobo: "교보문고",
  millie: "밀리의 서재",
  audible_jp: "Audible Japan",
};

/** "2015-01-04" -> "1월 4일", "2015-01" -> "1월" */
function formatPurchaseDate(value: string | null): string | null {
  if (!value) return null;
  const [, month, day] = value.split("-");
  if (!month) return null;
  const m = `${Number(month)}월`;
  return day ? `${m} ${Number(day)}일` : m;
}

export function BooklogContent() {
  const [years, setYears] = useState<number[]>([]);
  const [counts, setCounts] = useState<Record<string, number>>({});
  const [grandTotal, setGrandTotal] = useState(0);
  const [hasUnassigned, setHasUnassigned] = useState(false);

  const [activeYear, setActiveYear] = useState<Filter>("all");
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(1);

  const [items, setItems] = useState<BooklogItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .getBooklogYears()
      .then((d) => {
        setYears(d.years);
        setCounts(d.counts ?? {});
        setGrandTotal(d.total ?? 0);
        setHasUnassigned(d.has_unassigned);
      })
      .catch(() => setYears([]));
  }, []);

  // 검색어 입력 디바운스
  useEffect(() => {
    const t = setTimeout(() => {
      setQuery(search.trim());
      setPage(1);
    }, 300);
    return () => clearTimeout(t);
  }, [search]);

  const loadItems = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const d = await api.getBooklogItems({
        year: typeof activeYear === "number" ? activeYear : undefined,
        unassigned: activeYear === "unassigned" || undefined,
        q: query || undefined,
        page,
        limit: PAGE_SIZE,
      });
      setItems(d.items);
      setTotal(d.total);
    } catch (e) {
      setError(e instanceof Error ? e.message : "불러오기 실패");
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, [activeYear, query, page]);

  useEffect(() => {
    loadItems();
  }, [loadItems]);

  const selectYear = (y: Filter) => {
    setActiveYear(y);
    setPage(1);
  };

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  const chipClass = (active: boolean) =>
    `rounded-full px-3 py-1.5 text-sm font-medium transition ${
      active
        ? "bg-[var(--site-ink)] text-white"
        : "bg-white/80 text-[var(--site-muted)] ring-1 ring-[var(--site-border)] hover:bg-white"
    }`;

  return (
    <div className="space-y-8">
      <p className="text-sm leading-relaxed text-[var(--site-muted)]">
        2010년부터 읽고 사 모은 책 {grandTotal.toLocaleString()}권의 기록입니다. 2010–2018년은 직접
        정리해 둔 도서 DB와 Google Sites Booklog에서, 2021년 이후는 교보문고 주문 내역과 밀리의 서재·
        Audible Japan에서 옮겨 왔습니다.
      </p>

      <input
        type="search"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        placeholder="제목·저자·출판사 검색"
        className="w-full rounded-lg border border-[var(--site-border)] bg-white/90 px-4 py-2.5 text-sm text-[var(--site-ink)] shadow-sm outline-none placeholder:text-[var(--site-muted)] focus:ring-2 focus:ring-[var(--site-accent)]/30"
      />

      <div className="flex flex-wrap gap-2">
        <button type="button" onClick={() => selectYear("all")} className={chipClass(activeYear === "all")}>
          전체
        </button>
        {hasUnassigned && (
          <button
            type="button"
            onClick={() => selectYear("unassigned")}
            className={chipClass(activeYear === "unassigned")}
          >
            연도 미지정
          </button>
        )}
        {years.map((y) => (
          <button key={y} type="button" onClick={() => selectYear(y)} className={chipClass(activeYear === y)}>
            {y}
            <span className="ml-1.5 text-xs opacity-60">{counts[String(y)] ?? 0}</span>
          </button>
        ))}
      </div>

      {loading && (
        <div className="space-y-3">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-20 animate-pulse rounded-lg bg-black/5" />
          ))}
        </div>
      )}

      {error && (
        <Card className="border-destructive/40">
          <CardContent className="pt-6 text-sm text-destructive">{error}</CardContent>
        </Card>
      )}

      {!loading && !error && items.length === 0 && (
        <p className="text-sm text-[var(--site-muted)]">
          {query ? `"${query}"에 해당하는 책이 없습니다.` : "아직 등록된 도서가 없습니다."}
        </p>
      )}

      {!loading && !error && items.length > 0 && (
        <>
          <p className="text-xs text-[var(--site-muted)]">
            총 {total.toLocaleString()}권 · {page}/{totalPages} 페이지
          </p>

          <ul className="space-y-2">
            {items.map((it) => {
              const meta = [it.author, it.translator && `${it.translator} 譯`, it.publisher].filter(
                Boolean,
              );
              const purchased = formatPurchaseDate(it.purchase_date);
              return (
                <li key={it.id}>
                  <Card className="border-[var(--site-border)] bg-white/90 shadow-none">
                    <CardContent className="flex gap-4 py-3 sm:py-4">
                      {it.cover_url && (
                        // eslint-disable-next-line @next/next/no-img-element
                        <img
                          src={it.cover_url}
                          alt=""
                          loading="lazy"
                          className="h-20 w-14 shrink-0 rounded object-cover ring-1 ring-[var(--site-border)]"
                          onError={(e) => {
                            e.currentTarget.style.display = "none";
                          }}
                        />
                      )}
                      <div className="min-w-0 flex-1">
                        <div className="flex flex-wrap items-baseline gap-x-2 gap-y-1">
                          {it.year != null && (
                            <span className="text-xs font-semibold tabular-nums text-[var(--site-muted)]">
                              {it.year}
                              {purchased && ` · ${purchased}`}
                            </span>
                          )}
                          {it.source_url ? (
                            <a
                              href={it.source_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="font-medium text-[var(--site-ink)] underline-offset-4 hover:underline"
                            >
                              {it.title}
                            </a>
                          ) : (
                            <span className="font-medium text-[var(--site-ink)]">{it.title}</span>
                          )}
                        </div>
                        {meta.length > 0 && (
                          <p className="mt-1 text-sm text-[var(--site-muted)]">{meta.join(" · ")}</p>
                        )}
                        {(it.note || it.source) && (
                          <p className="mt-1 text-xs text-[var(--site-muted)]">
                            {[it.note, it.source ? SOURCE_LABEL[it.source] ?? it.source : null]
                              .filter(Boolean)
                              .join(" · ")}
                          </p>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                </li>
              );
            })}
          </ul>

          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-3">
              <button
                type="button"
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className="rounded-full px-4 py-2 text-sm font-medium text-[var(--site-muted)] ring-1 ring-[var(--site-border)] transition hover:bg-white disabled:opacity-40"
              >
                ← 이전
              </button>
              <span className="text-sm tabular-nums text-[var(--site-muted)]">
                {page} / {totalPages}
              </span>
              <button
                type="button"
                disabled={page >= totalPages}
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                className="rounded-full px-4 py-2 text-sm font-medium text-[var(--site-muted)] ring-1 ring-[var(--site-border)] transition hover:bg-white disabled:opacity-40"
              >
                다음 →
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
