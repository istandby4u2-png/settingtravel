"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { api } from "@/lib/api";

type SourceFilter = "all" | "brunch" | "naver";

interface BlogListPost {
  id: number;
  source: string;
  title: string;
  excerpt: string;
  url: string;
  published_date: string | null;
  thumbnail: string | null;
  scraped_at: string | null;
}

export default function BlogPage() {
  const [posts, setPosts] = useState<BlogListPost[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [filter, setFilter] = useState<SourceFilter>("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const limit = 12;
  const sourceArg = filter === "all" ? undefined : filter;

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getBlogPosts(sourceArg, page, limit);
      setPosts(data.posts);
      setTotal(data.total);
    } catch (e) {
      setError(e instanceof Error ? e.message : "글을 불러오지 못했습니다.");
      setPosts([]);
    } finally {
      setLoading(false);
    }
  }, [sourceArg, page]);

  useEffect(() => {
    load();
  }, [load]);

  const totalPages = Math.max(1, Math.ceil(total / limit));

  return (
    <div className="min-h-[60vh] bg-[var(--site-paper)]">
      <div className="p-8 max-w-4xl mx-auto space-y-10">
        <header className="space-y-3 text-center sm:text-left">
          <p className="text-xs font-medium uppercase tracking-[0.2em] text-muted-foreground">
            Setting travel
          </p>
          <h1 className="text-3xl sm:text-4xl font-bold tracking-tight text-balance">
            다정한 여행의 배경
          </h1>
          <p className="text-muted-foreground max-w-2xl leading-relaxed">
            책·영화·드라마 속 그곳을 찾아 떠나는 기록입니다. 브런치와 네이버 블로그에서 수집한 글을
            한곳에서 읽을 수 있습니다.
          </p>
        </header>

        <Tabs
          value={filter}
          onValueChange={(v) => {
            setFilter(v as SourceFilter);
            setPage(1);
          }}
          className="w-full"
        >
          <TabsList className="grid w-full max-w-md grid-cols-3">
            <TabsTrigger value="all">전체</TabsTrigger>
            <TabsTrigger value="brunch">Brunch</TabsTrigger>
            <TabsTrigger value="naver">네이버</TabsTrigger>
          </TabsList>

          <TabsContent value="all" className="mt-8 space-y-6">
            <PostGrid posts={posts} loading={loading} error={error} />
          </TabsContent>
          <TabsContent value="brunch" className="mt-8 space-y-6">
            <PostGrid posts={posts} loading={loading} error={error} />
          </TabsContent>
          <TabsContent value="naver" className="mt-8 space-y-6">
            <PostGrid posts={posts} loading={loading} error={error} />
          </TabsContent>
        </Tabs>

        {!loading && !error && totalPages > 1 && (
          <div className="flex items-center justify-center gap-3 pt-4">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
            >
              이전
            </Button>
            <span className="text-sm text-muted-foreground tabular-nums">
              {page} / {totalPages}
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages}
            >
              다음
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}

function PostGrid({
  posts,
  loading,
  error,
}: {
  posts: BlogListPost[];
  loading: boolean;
  error: string | null;
}) {
  if (loading) {
    return (
      <div className="grid gap-4 sm:grid-cols-2">
        {[1, 2, 3, 4].map((i) => (
          <Card key={i} className="overflow-hidden animate-pulse">
            <CardHeader className="space-y-2">
              <div className="h-4 w-24 rounded bg-muted" />
              <div className="h-6 w-full rounded bg-muted" />
            </CardHeader>
            <CardContent>
              <div className="h-16 w-full rounded bg-muted" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <Card className="border-destructive/50">
        <CardContent className="pt-6">
          <p className="text-destructive text-sm leading-relaxed">{error}</p>
          <p className="text-muted-foreground text-sm mt-2">
            백엔드가 실행 중인지 확인해 주세요. 로컬에서는{" "}
            <code className="rounded bg-muted px-1.5 py-0.5 text-xs">uvicorn main:app --reload</code> 로
            API를 띄운 뒤 새로고침해 보세요.
          </p>
        </CardContent>
      </Card>
    );
  }

  if (posts.length === 0) {
    return (
      <Card>
        <CardContent className="py-12 text-center text-muted-foreground text-sm">
          아직 수집된 글이 없습니다. 관리 메뉴의 <strong>스크래핑</strong>에서 글을 먼저 가져오세요.
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2">
      {posts.map((post) => (
        <Link key={post.id} href={`/blog/${post.id}`} className="group block">
          <Card className="h-full overflow-hidden transition-shadow hover:shadow-md hover:border-primary/20">
            {post.thumbnail && (
              <div className="relative aspect-[16/9] w-full overflow-hidden bg-muted">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={post.thumbnail}
                  alt={post.title || ""}
                  className="absolute inset-0 h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
                  loading="lazy"
                />
              </div>
            )}
            <CardHeader className="space-y-2">
              <div className="flex items-center gap-2">
                <SourceBadge source={post.source} />
                {post.published_date && (
                  <span className="text-xs text-muted-foreground">{post.published_date}</span>
                )}
              </div>
              <h2 className="text-lg font-semibold leading-snug group-hover:text-primary transition-colors line-clamp-2">
                {post.title || "제목 없음"}
              </h2>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground leading-relaxed line-clamp-3">{post.excerpt}</p>
            </CardContent>
          </Card>
        </Link>
      ))}
    </div>
  );
}

function SourceBadge({ source }: { source: string }) {
  if (source === "brunch") {
    return (
      <Badge variant="secondary" className="text-[10px] font-semibold uppercase tracking-wide">
        Brunch
      </Badge>
    );
  }
  if (source === "naver") {
    return (
      <Badge variant="outline" className="text-[10px] font-semibold border-emerald-600/40 text-emerald-800 dark:text-emerald-400">
        네이버
      </Badge>
    );
  }
  return <Badge variant="outline">{source}</Badge>;
}
