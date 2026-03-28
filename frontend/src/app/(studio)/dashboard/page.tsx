"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";

interface ScrapeStatus {
  total_posts: number;
  db_brunch_count: number;
  db_naver_count: number;
  is_running: boolean;
  progress: string;
}

interface AnalysisData {
  id: number;
  analysis: {
    statistical?: {
      total_posts: number;
      avg_post_length: number;
      avg_sentence_length: number;
      ending_style: Record<string, number>;
    };
    ai_analysis?: {
      overall_tone?: string;
      writing_persona?: string;
      content_themes?: string[];
    };
  };
  created_at: string;
}

interface GenerationHistory {
  posts: Array<{ id: number; topic: string; created_at: string }>;
}

export default function DashboardPage() {
  const [scrapeStatus, setScrapeStatus] = useState<ScrapeStatus | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisData | null>(null);
  const [genHistory, setGenHistory] = useState<GenerationHistory | null>(null);
  const [backendUp, setBackendUp] = useState<boolean | null>(null);

  useEffect(() => {
    api.health().then(() => setBackendUp(true)).catch(() => setBackendUp(false));
    api.getScrapeStatus().then((d) => setScrapeStatus(d as ScrapeStatus)).catch(() => {});
    api.getLatestAnalysis().then((d) => setAnalysis(d as AnalysisData)).catch(() => {});
    api.getGenerationHistory().then((d) => setGenHistory(d as GenerationHistory)).catch(() => {});
  }, []);

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">대시보드</h1>
        <p className="text-muted-foreground mt-1">블로그 문체 분석 및 자동 생성 서비스 현황</p>
      </div>

      {backendUp === false && (
        <Card className="border-destructive">
          <CardContent className="pt-6">
            <p className="text-destructive font-medium">
              백엔드 서버에 연결할 수 없습니다. 
              <code className="mx-1 px-2 py-0.5 bg-muted rounded text-sm">
                cd backend &amp;&amp; uvicorn main:app --reload
              </code>
              명령으로 서버를 시작해주세요.
            </p>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              수집된 글
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {scrapeStatus?.total_posts ?? "—"}
            </div>
            <div className="flex gap-2 mt-2">
              <Badge variant="secondary">
                브런치 {scrapeStatus?.db_brunch_count ?? 0}
              </Badge>
              <Badge variant="secondary">
                네이버 {scrapeStatus?.db_naver_count ?? 0}
              </Badge>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              문체 분석
            </CardTitle>
          </CardHeader>
          <CardContent>
            {analysis && !("error" in analysis) ? (
              <>
                <div className="text-3xl font-bold">완료</div>
                <p className="text-sm text-muted-foreground mt-1">
                  {analysis.analysis?.ai_analysis?.overall_tone || "분석 결과 있음"}
                </p>
              </>
            ) : (
              <>
                <div className="text-3xl font-bold text-muted-foreground">미완료</div>
                <p className="text-sm text-muted-foreground mt-1">
                  글 수집 후 분석을 실행해주세요
                </p>
              </>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              생성된 글
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {genHistory?.posts?.length ?? 0}
            </div>
            <p className="text-sm text-muted-foreground mt-1">
              AI로 생성한 블로그 글
            </p>
          </CardContent>
        </Card>
      </div>

      {scrapeStatus?.is_running && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">스크래핑 진행 중</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-3">
              <div className="h-2 w-2 rounded-full bg-primary animate-pulse" />
              <span className="text-sm">{scrapeStatus.progress}</span>
            </div>
          </CardContent>
        </Card>
      )}

      {analysis?.analysis?.statistical && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">문체 분석 요약</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-sm text-muted-foreground">분석 글 수</p>
                <p className="text-lg font-semibold">
                  {analysis.analysis.statistical.total_posts}편
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">평균 글 길이</p>
                <p className="text-lg font-semibold">
                  {analysis.analysis.statistical.avg_post_length?.toLocaleString()}자
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">평균 문장 길이</p>
                <p className="text-lg font-semibold">
                  {analysis.analysis.statistical.avg_sentence_length}자
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">톤</p>
                <p className="text-lg font-semibold">
                  {analysis.analysis.ai_analysis?.overall_tone || "—"}
                </p>
              </div>
            </div>

            {analysis.analysis.ai_analysis?.content_themes && (
              <div>
                <p className="text-sm text-muted-foreground mb-2">주요 주제</p>
                <div className="flex flex-wrap gap-2">
                  {analysis.analysis.ai_analysis.content_themes.map((theme, i) => (
                    <Badge key={i} variant="outline">{theme}</Badge>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {genHistory?.posts && genHistory.posts.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">최근 생성된 글</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {genHistory.posts.slice(0, 5).map((post) => (
                <div key={post.id} className="flex items-center justify-between py-2 border-b border-border last:border-0">
                  <span className="font-medium">{post.topic}</span>
                  <span className="text-sm text-muted-foreground">
                    {post.created_at ? new Date(post.created_at).toLocaleDateString("ko-KR") : ""}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
