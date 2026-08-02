"use client";

import { useEffect, useState, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { api } from "@/lib/api";

interface Post {
  id: number;
  source: string;
  title: string;
  content: string;
  url: string;
  published_date: string;
  scraped_at: string;
}

interface PostsResponse {
  posts: Post[];
  total: number;
  page: number;
}

interface ScrapeStatus {
  is_running: boolean;
  progress: string;
  total_posts: number;
  db_brunch_count: number;
  db_naver_count: number;
  error: string | null;
}

export default function ScrapePage() {
  const [status, setStatus] = useState<ScrapeStatus | null>(null);
  const [posts, setPosts] = useState<Post[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [source, setSource] = useState<string | undefined>(undefined);
  const [selectedPost, setSelectedPost] = useState<Post | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchStatus = useCallback(async () => {
    try {
      const data = (await api.getScrapeStatus()) as ScrapeStatus;
      setStatus(data);
    } catch {
      /* ignore */
    }
  }, []);

  const fetchPosts = useCallback(async () => {
    try {
      const data = (await api.getPosts(source, page)) as PostsResponse;
      setPosts(data.posts);
      setTotal(data.total);
    } catch {
      /* ignore */
    }
  }, [source, page]);

  useEffect(() => {
    fetchStatus();
    fetchPosts();
  }, [fetchStatus, fetchPosts]);

  useEffect(() => {
    if (!status?.is_running) return;
    const interval = setInterval(fetchStatus, 3000);
    return () => clearInterval(interval);
  }, [status?.is_running, fetchStatus]);

  const startScraping = async () => {
    setLoading(true);
    try {
      await api.startScraping();
      await fetchStatus();
    } finally {
      setLoading(false);
    }
  };

  const viewPost = async (id: number) => {
    try {
      const data = (await api.getPostDetail(id)) as Post;
      setSelectedPost(data);
    } catch {
      /* ignore */
    }
  };

  const totalPages = Math.ceil(total / 20);

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">스크래핑 관리</h1>
          <p className="text-muted-foreground mt-1">
            브런치와 네이버 블로그에서 글을 수집합니다
          </p>
        </div>
        <div className="flex flex-wrap gap-2 justify-end">
          <Button variant="outline" asChild>
            <a href={api.getExportUrl("json")} download>
              JSON 내보내기
            </a>
          </Button>
          <Button variant="outline" asChild>
            <a href={api.getExportUrl("markdown")} download>
              Markdown(zip)
            </a>
          </Button>
          <Button
            onClick={startScraping}
            disabled={loading || status?.is_running}
            size="lg"
          >
            {status?.is_running ? "수집 중..." : "스크래핑 시작"}
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">전체 글</div>
            <div className="text-2xl font-bold mt-1">{status?.total_posts ?? 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">브런치</div>
            <div className="text-2xl font-bold mt-1">{status?.db_brunch_count ?? 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">네이버</div>
            <div className="text-2xl font-bold mt-1">{status?.db_naver_count ?? 0}</div>
          </CardContent>
        </Card>
      </div>

      {status?.is_running && (
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="h-2 w-2 rounded-full bg-primary animate-pulse" />
              <span className="text-sm">{status.progress}</span>
            </div>
          </CardContent>
        </Card>
      )}

      {status?.error && (
        <Card className="border-destructive">
          <CardContent className="pt-6">
            <p className="text-destructive text-sm">{status.error}</p>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>수집된 글 목록</CardTitle>
        </CardHeader>
        <CardContent>
          <Tabs
            defaultValue="all"
            onValueChange={(v) => {
              setSource(v === "all" ? undefined : v);
              setPage(1);
            }}
          >
            <TabsList>
              <TabsTrigger value="all">전체</TabsTrigger>
              <TabsTrigger value="brunch">브런치</TabsTrigger>
              <TabsTrigger value="naver">네이버</TabsTrigger>
            </TabsList>

            <TabsContent value="all" className="mt-4">
              <PostList posts={posts} onView={viewPost} />
            </TabsContent>
            <TabsContent value="brunch" className="mt-4">
              <PostList posts={posts} onView={viewPost} />
            </TabsContent>
            <TabsContent value="naver" className="mt-4">
              <PostList posts={posts} onView={viewPost} />
            </TabsContent>
          </Tabs>

          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2 mt-4">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
              >
                이전
              </Button>
              <span className="text-sm text-muted-foreground">
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
        </CardContent>
      </Card>

      {selectedPost && (
        <Card>
          <CardHeader className="flex flex-row items-start justify-between">
            <div>
              <CardTitle>{selectedPost.title || "제목 없음"}</CardTitle>
              <div className="flex gap-2 mt-2">
                <Badge>{selectedPost.source}</Badge>
                {selectedPost.published_date && (
                  <Badge variant="outline">{selectedPost.published_date}</Badge>
                )}
              </div>
            </div>
            <Button variant="ghost" size="sm" onClick={() => setSelectedPost(null)}>
              닫기
            </Button>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-96">
              <div className="whitespace-pre-wrap text-sm leading-relaxed">
                {selectedPost.content}
              </div>
            </ScrollArea>
            {selectedPost.url && (
              <a
                href={selectedPost.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-primary hover:underline mt-4 inline-block"
              >
                원본 보기 →
              </a>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function PostList({
  posts,
  onView,
}: {
  posts: Post[];
  onView: (id: number) => void;
}) {
  if (posts.length === 0) {
    return (
      <p className="text-muted-foreground text-sm py-8 text-center">
        수집된 글이 없습니다. 스크래핑을 실행해주세요.
      </p>
    );
  }

  return (
    <div className="space-y-2">
      {posts.map((post) => (
        <div
          key={post.id}
          className="flex items-center justify-between p-3 rounded-lg border border-border hover:bg-accent cursor-pointer transition-colors"
          onClick={() => onView(post.id)}
        >
          <div className="flex-1 min-w-0 mr-4">
            <p className="font-medium truncate">{post.title || "제목 없음"}</p>
            <p className="text-sm text-muted-foreground truncate mt-0.5">
              {post.content}
            </p>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <Badge variant="outline" className="text-xs">
              {post.source}
            </Badge>
          </div>
        </div>
      ))}
    </div>
  );
}
