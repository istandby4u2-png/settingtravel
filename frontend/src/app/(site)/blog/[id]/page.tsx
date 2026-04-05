"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { api } from "@/lib/api";

interface BlogPost {
  id: number;
  source: string;
  title: string;
  content: string;
  url: string;
  published_date: string | null;
  thumbnail: string | null;
  images: string[] | null;
  scraped_at: string | null;
}

export default function BlogPostPage() {
  const params = useParams();
  const idParam = params?.id;
  const id = typeof idParam === "string" ? parseInt(idParam, 10) : NaN;

  const [post, setPost] = useState<BlogPost | null | undefined>(undefined);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!Number.isFinite(id)) {
      setPost(null);
      return;
    }

    let cancelled = false;
    (async () => {
      try {
        const data = await api.getBlogPost(id);
        if (!cancelled) {
          setPost(data);
          setError(null);
          if (data?.title) {
            document.title = `${data.title} | 배경여행`;
          }
        }
      } catch (e) {
        if (!cancelled) {
          setPost(null);
          setError(e instanceof Error ? e.message : "불러오기 실패");
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [id]);

  if (post === undefined) {
    return (
      <div className="p-8 max-w-3xl mx-auto">
        <div className="animate-pulse space-y-4">
          <div className="h-8 w-48 rounded bg-muted" />
          <div className="h-64 w-full rounded bg-muted" />
        </div>
      </div>
    );
  }

  if (post === null) {
    return (
      <div className="p-8 max-w-3xl mx-auto space-y-6">
        <Button variant="ghost" size="sm" asChild className="gap-2 -ml-2">
          <Link href="/blog">
            <ArrowLeft className="size-4" />
            목록으로
          </Link>
        </Button>
        <Card className="border-destructive/50">
          <CardContent className="pt-8 pb-8 text-center space-y-2">
            <p className="font-medium">
              {error || "글을 찾을 수 없습니다."}
            </p>
            <p className="text-sm text-muted-foreground">
              주소가 올바른지 확인하거나 목록에서 다시 선택해 주세요.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <article className="min-h-[60vh] bg-[var(--site-paper)]">
      <div className="p-6 sm:p-10 max-w-3xl mx-auto space-y-8">
        <div className="flex flex-wrap items-center gap-3">
          <Button variant="ghost" size="sm" asChild className="gap-2 -ml-2 shrink-0">
            <Link href="/blog">
              <ArrowLeft className="size-4" />
              목록으로
            </Link>
          </Button>
        </div>

        <header className="space-y-4">
          <div className="flex flex-wrap items-center gap-2">
            <SourceBadge source={post.source} />
            {post.published_date && (
              <span className="text-sm text-muted-foreground">{post.published_date}</span>
            )}
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold tracking-tight text-balance leading-tight">
            {post.title || "제목 없음"}
          </h1>
          <p className="text-sm text-muted-foreground">
            원본이 궁금하시면 아래 링크에서 서식·이미지를 함께 확인할 수 있습니다.
          </p>
          <a
            href={post.url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex text-sm font-medium text-primary hover:underline"
          >
            원문 보기 →
          </a>
        </header>

        {post.thumbnail && (
          <div className="rounded-lg overflow-hidden border border-border/60">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={post.thumbnail}
              alt={post.title || ""}
              className="w-full max-h-[480px] object-cover"
            />
          </div>
        )}

        <Card className="border-border/80 shadow-sm">
          <CardContent className="pt-6 sm:pt-8 pb-8 space-y-6">
            <div className="text-base leading-[1.75] text-foreground/90 whitespace-pre-wrap break-words">
              {post.content}
            </div>

            {post.images && post.images.length > 0 && (
              <div className="space-y-4 pt-4 border-t border-border/50">
                <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  본문 이미지
                </p>
                <div className="grid gap-3">
                  {post.images.map((src, i) => (
                    <div key={i} className="rounded-lg overflow-hidden border border-border/40">
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img
                        src={src}
                        alt={`${post.title} 이미지 ${i + 1}`}
                        className="w-full object-contain"
                        loading="lazy"
                      />
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </article>
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
      <Badge
        variant="outline"
        className="text-[10px] font-semibold border-emerald-600/40 text-emerald-800 dark:text-emerald-400"
      >
        네이버 블로그
      </Badge>
    );
  }
  return <Badge variant="outline">{source}</Badge>;
}
