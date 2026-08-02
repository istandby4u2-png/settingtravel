"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import { api } from "@/lib/api";

interface GeneratedResult {
  id: number;
  title: string;
  content: string;
  topic: string;
  length: string;
  char_count: number;
  created_at: string;
  reference_url?: string | null;
  error?: string;
}

interface HistoryPost {
  id: number;
  topic: string;
  content: string;
  created_at: string;
}

export default function GeneratePage() {
  const [topic, setTopic] = useState("");
  const [length, setLength] = useState("medium");
  const [instructions, setInstructions] = useState("");
  const [referenceUrl, setReferenceUrl] = useState("");
  const [result, setResult] = useState<GeneratedResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<HistoryPost[]>([]);
  const [selectedHistory, setSelectedHistory] = useState<HistoryPost | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    api
      .getGenerationHistory()
      .then((d) => {
        const data = d as { posts: HistoryPost[] };
        setHistory(data.posts || []);
      })
      .catch(() => {});
  }, []);

  const generate = async () => {
    if (!topic.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = (await api.generatePost({
        topic: topic.trim(),
        length,
        additional_instructions: instructions.trim(),
        reference_url: referenceUrl.trim(),
      })) as GeneratedResult;
      if (data.error) {
        setError(data.error);
      } else {
        setResult(data);
        api
          .getGenerationHistory()
          .then((d) => setHistory((d as { posts: HistoryPost[] }).posts || []))
          .catch(() => {});
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "글 생성 중 오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const viewHistoryPost = async (id: number) => {
    try {
      const data = (await api.getGeneratedPost(id)) as HistoryPost;
      setSelectedHistory(data);
    } catch {
      /* ignore */
    }
  };

  const displayContent = selectedHistory?.content || (result ? `# ${result.title}\n\n${result.content}` : null);
  const displayTitle = selectedHistory ? selectedHistory.topic : result?.title;

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">글 생성</h1>
        <p className="text-muted-foreground mt-1">
          분석된 문체로 새로운 블로그 글을 생성합니다
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>새 글 생성</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="topic">주제</Label>
                <Input
                  id="topic"
                  placeholder="예: 제주도 카페 투어, 가을 단풍 여행기..."
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !loading) generate();
                  }}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>글 길이</Label>
                  <Select value={length} onValueChange={setLength}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="short">짧게 (800~1,200자)</SelectItem>
                      <SelectItem value="medium">보통 (1,500~2,500자)</SelectItem>
                      <SelectItem value="long">길게 (3,000~5,000자)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="referenceUrl">참조 문서 URL (선택)</Label>
                <Input
                  id="referenceUrl"
                  type="url"
                  placeholder="예: https://brunch.co.kr/@istandby4u2/147"
                  value={referenceUrl}
                  onChange={(e) => setReferenceUrl(e.target.value)}
                />
                <p className="text-xs text-muted-foreground">
                  특정 글의 스타일을 참고하여 생성합니다. 블로그, 기사 등 URL을 입력하세요.
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="instructions">추가 지시사항 (선택)</Label>
                <Textarea
                  id="instructions"
                  placeholder="예: 음식 사진 묘사를 많이 넣어주세요, 독자에게 질문을 던지는 형식으로..."
                  value={instructions}
                  onChange={(e) => setInstructions(e.target.value)}
                  rows={3}
                />
              </div>

              <Button onClick={generate} disabled={loading || !topic.trim()} className="w-full" size="lg">
                {loading ? "생성 중..." : "글 생성하기"}
              </Button>
            </CardContent>
          </Card>

          {error && (
            <Card className="border-destructive">
              <CardContent className="pt-6">
                <p className="text-destructive text-sm">{error}</p>
              </CardContent>
            </Card>
          )}

          {loading && (
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-3">
                  <div className="h-2 w-2 rounded-full bg-primary animate-pulse" />
                  <span className="text-sm">
                    AI가 글을 작성하고 있습니다. 잠시만 기다려주세요...
                  </span>
                </div>
              </CardContent>
            </Card>
          )}

          {displayContent && (
            <Card>
              <CardHeader className="flex flex-row items-start justify-between">
                <div>
                  <CardTitle>{displayTitle || "생성된 글"}</CardTitle>
                  {result && (
                    <div className="flex flex-wrap gap-2 mt-2">
                      <Badge variant="outline">{result.char_count?.toLocaleString()}자</Badge>
                      <Badge variant="secondary">
                        {length === "short" ? "짧게" : length === "long" ? "길게" : "보통"}
                      </Badge>
                      {result.reference_url && (
                        <Badge variant="outline" className="text-blue-600 border-blue-300">
                          <a
                            href={result.reference_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="hover:underline"
                          >
                            참조 문서
                          </a>
                        </Badge>
                      )}
                    </div>
                  )}
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => copyToClipboard(displayContent)}
                  >
                    {copied ? "복사됨!" : "복사"}
                  </Button>
                  {selectedHistory && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setSelectedHistory(null)}
                    >
                      닫기
                    </Button>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-[500px]">
                  <div className="whitespace-pre-wrap text-sm leading-relaxed pr-4">
                    {displayContent}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>
          )}
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">생성 히스토리</CardTitle>
            </CardHeader>
            <CardContent>
              {history.length === 0 ? (
                <p className="text-sm text-muted-foreground text-center py-4">
                  아직 생성된 글이 없습니다.
                </p>
              ) : (
                <div className="space-y-2">
                  {history.map((post) => (
                    <div
                      key={post.id}
                      className="p-3 rounded-lg border border-border hover:bg-accent cursor-pointer transition-colors"
                      onClick={() => viewHistoryPost(post.id)}
                    >
                      <p className="font-medium text-sm truncate">{post.topic}</p>
                      <p className="text-xs text-muted-foreground mt-1">
                        {post.created_at
                          ? new Date(post.created_at).toLocaleDateString("ko-KR")
                          : ""}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
