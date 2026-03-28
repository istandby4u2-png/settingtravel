"use client";

import { useCallback, useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { api } from "@/lib/api";

type Item = {
  id: number;
  year: number | null;
  title: string;
  author: string | null;
  note: string | null;
  source_url: string | null;
};

export function BooklogContent() {
  const [years, setYears] = useState<number[]>([]);
  const [hasUnassigned, setHasUnassigned] = useState(false);
  const [activeYear, setActiveYear] = useState<number | "all" | "unassigned">("all");
  const [items, setItems] = useState<Item[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadYears = useCallback(async () => {
    try {
      const d = await api.getBooklogYears();
      setYears(d.years);
      setHasUnassigned(d.has_unassigned);
    } catch {
      setYears([]);
    }
  }, []);

  const loadItems = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const opts =
        activeYear === "all"
          ? { limit: 300, page: 1 }
          : activeYear === "unassigned"
            ? { unassigned: true, limit: 300, page: 1 }
            : { year: activeYear as number, limit: 300, page: 1 };
      const d = await api.getBooklogItems(opts);
      setItems(d.items);
      setTotal(d.total);
    } catch (e) {
      setError(e instanceof Error ? e.message : "불러오기 실패");
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, [activeYear]);

  useEffect(() => {
    loadYears();
  }, [loadYears]);

  useEffect(() => {
    loadItems();
  }, [loadItems]);

  return (
    <div className="space-y-8">
      <p className="text-sm leading-relaxed text-[var(--site-muted)]">
        아래 목록은 Google Sites에 공개되어 있던 <strong>도서(Genre·book)</strong> 항목을 옮긴 것입니다. 연도는
        기존 Booklog 메뉴(2010–2017)에 맞춰 <strong>순환 배치한 추정치</strong>이므로, 정확한 독서 연도는 원문
        사이트를 참고해 주세요.
      </p>

      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => setActiveYear("all")}
          className={`rounded-full px-3 py-1.5 text-sm font-medium transition ${
            activeYear === "all"
              ? "bg-[var(--site-ink)] text-white"
              : "bg-white/80 text-[var(--site-muted)] ring-1 ring-[var(--site-border)] hover:bg-white"
          }`}
        >
          전체
        </button>
        {hasUnassigned && (
          <button
            type="button"
            onClick={() => setActiveYear("unassigned")}
            className={`rounded-full px-3 py-1.5 text-sm font-medium transition ${
              activeYear === "unassigned"
                ? "bg-[var(--site-ink)] text-white"
                : "bg-white/80 text-[var(--site-muted)] ring-1 ring-[var(--site-border)] hover:bg-white"
            }`}
          >
            연도 미지정
          </button>
        )}
        {years.map((y) => (
          <button
            key={y}
            type="button"
            onClick={() => setActiveYear(y)}
            className={`rounded-full px-3 py-1.5 text-sm font-medium transition ${
              activeYear === y
                ? "bg-[var(--site-ink)] text-white"
                : "bg-white/80 text-[var(--site-muted)] ring-1 ring-[var(--site-border)] hover:bg-white"
            }`}
          >
            {y}
          </button>
        ))}
      </div>

      {loading && (
        <div className="space-y-3">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-14 animate-pulse rounded-lg bg-black/5" />
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
          아직 등록된 도서가 없습니다. 백엔드에서 시드를 실행했는지 확인해 주세요.{" "}
          <code className="rounded bg-black/5 px-1 text-xs">python3 scripts/seed_booklog.py</code>
        </p>
      )}

      {!loading && !error && items.length > 0 && (
        <>
          <p className="text-xs text-[var(--site-muted)]">총 {total}권 (현재 필터)</p>
          <ul className="space-y-2">
          {items.map((it) => (
            <li key={it.id}>
              <Card className="border-[var(--site-border)] bg-white/90 shadow-none">
                <CardContent className="py-3 sm:py-4">
                  <div className="flex flex-wrap items-baseline gap-x-2 gap-y-1">
                    {it.year != null && (
                      <span className="text-xs font-semibold tabular-nums text-[var(--site-muted)]">
                        {it.year}
                      </span>
                    )}
                    <span className="font-medium text-[var(--site-ink)]">{it.title}</span>
                  </div>
                  {it.author && (
                    <p className="mt-1 text-sm text-[var(--site-muted)]">{it.author}</p>
                  )}
                </CardContent>
              </Card>
            </li>
          ))}
        </ul>
        </>
      )}
    </div>
  );
}
