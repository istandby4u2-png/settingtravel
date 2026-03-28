"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";

export function HomeLatestEssays() {
  const [posts, setPosts] = useState<
    Array<{ id: number; title: string; excerpt: string; source: string; published_date: string | null }>
  >([]);
  const [err, setErr] = useState(false);

  useEffect(() => {
    api
      .getBlogPosts(undefined, 1, 3)
      .then((d) => setPosts(d.posts))
      .catch(() => setErr(true));
  }, []);

  if (err || posts.length === 0) return null;

  return (
    <section className="mx-auto max-w-5xl px-4 sm:px-6">
      <div className="grid gap-4 sm:grid-cols-3">
        {posts.map((p) => (
          <Link key={p.id} href={`/blog/${p.id}`}>
            <Card className="h-full border-[var(--site-border)] bg-white/80 transition-shadow hover:shadow-md">
              <CardHeader className="space-y-2 pb-2">
                <Badge variant="secondary" className="w-fit text-[10px] uppercase">
                  {p.source}
                </Badge>
                <h3 className="line-clamp-2 text-base font-medium leading-snug text-[var(--site-ink)]">
                  {p.title || "제목 없음"}
                </h3>
              </CardHeader>
              <CardContent>
                <p className="line-clamp-3 text-sm text-[var(--site-muted)]">{p.excerpt}</p>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
      <div className="mt-8 text-center">
        <Link
          href="/blog"
          className="text-sm font-medium text-[var(--site-accent)] underline-offset-4 hover:underline"
        >
          View all →
        </Link>
      </div>
    </section>
  );
}
