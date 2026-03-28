"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { api } from "@/lib/api";

interface EndingStyle {
  [key: string]: number;
}

interface FreqItem {
  word?: string;
  phrase?: string;
  count: number;
}

interface StatisticalAnalysis {
  total_posts: number;
  avg_post_length: number;
  avg_sentence_length: number;
  min_sentence_length: number;
  max_sentence_length: number;
  avg_paragraph_length: number;
  avg_paragraphs_per_post: number;
  ending_style: EndingStyle;
  frequent_words: FreqItem[];
  frequent_expressions: FreqItem[];
  emoji_total: number;
  emoji_per_post: number;
}

interface AIAnalysis {
  overall_tone?: string;
  writing_persona?: string;
  narrative_style?: string;
  vocabulary_level?: string;
  sentence_structure?: string;
  paragraph_organization?: string;
  rhetorical_devices?: string[];
  emotional_expression?: string;
  topic_transition?: string;
  opening_pattern?: string;
  closing_pattern?: string;
  unique_characteristics?: string[];
  content_themes?: string[];
  reader_engagement?: string;
  error?: string;
}

interface AnalysisResult {
  id?: number;
  analysis: {
    statistical: StatisticalAnalysis;
    ai_analysis: AIAnalysis;
  };
  created_at?: string;
  error?: string;
}

export default function AnalysisPage() {
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .getLatestAnalysis()
      .then((d) => {
        const data = d as AnalysisResult;
        if (!data.error) setAnalysis(data);
      })
      .catch(() => {});
  }, []);

  const runAnalysis = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = (await api.runAnalysis()) as AnalysisResult;
      if (data.error) {
        setError(data.error);
      } else {
        setAnalysis(data);
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "분석 실행 중 오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  };

  const stats = analysis?.analysis?.statistical;
  const ai = analysis?.analysis?.ai_analysis;

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">문체 분석</h1>
          <p className="text-muted-foreground mt-1">
            수집된 글의 문체와 스타일을 분석합니다
          </p>
        </div>
        <Button onClick={runAnalysis} disabled={loading} size="lg">
          {loading ? "분석 중..." : "분석 실행"}
        </Button>
      </div>

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
                글을 분석하고 있습니다. Gemini AI 분석을 포함하여 1-2분 정도 소요될 수 있습니다...
              </span>
            </div>
          </CardContent>
        </Card>
      )}

      {stats && (
        <>
          <Card>
            <CardHeader>
              <CardTitle>통계 분석</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                <StatBox label="분석 글 수" value={`${stats.total_posts}편`} />
                <StatBox label="평균 글 길이" value={`${stats.avg_post_length?.toLocaleString()}자`} />
                <StatBox label="평균 문장 길이" value={`${stats.avg_sentence_length}자`} />
                <StatBox label="글당 평균 문단" value={`${stats.avg_paragraphs_per_post}개`} />
                <StatBox label="최소 문장 길이" value={`${stats.min_sentence_length}자`} />
                <StatBox label="최대 문장 길이" value={`${stats.max_sentence_length}자`} />
                <StatBox label="이모지 총 사용" value={`${stats.emoji_total}개`} />
                <StatBox label="글당 이모지" value={`${stats.emoji_per_post}개`} />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>종결어미 분포</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {Object.entries(stats.ending_style || {})
                  .sort(([, a], [, b]) => b - a)
                  .map(([style, pct]) => (
                    <div key={style} className="flex items-center gap-3">
                      <span className="text-sm font-medium w-24">{style}</span>
                      <div className="flex-1 h-6 bg-muted rounded-full overflow-hidden">
                        <div
                          className="h-full bg-primary rounded-full transition-all"
                          style={{ width: `${Math.min(pct, 100)}%` }}
                        />
                      </div>
                      <span className="text-sm text-muted-foreground w-14 text-right">
                        {pct}%
                      </span>
                    </div>
                  ))}
              </div>
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>자주 사용하는 단어</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {stats.frequent_words?.slice(0, 20).map((item, i) => (
                    <Badge key={i} variant={i < 5 ? "default" : "secondary"}>
                      {item.word} ({item.count})
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>자주 사용하는 표현</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {stats.frequent_expressions?.slice(0, 15).map((item, i) => (
                    <Badge key={i} variant={i < 3 ? "default" : "outline"}>
                      {item.phrase} ({item.count})
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </>
      )}

      {ai && !ai.error && (
        <Card>
          <CardHeader>
            <CardTitle>AI 문체 분석 (Gemini)</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {ai.overall_tone && (
                <AIField label="전체 톤" value={ai.overall_tone} />
              )}
              {ai.writing_persona && (
                <AIField label="글쓴이 페르소나" value={ai.writing_persona} />
              )}
              {ai.narrative_style && (
                <AIField label="서술 방식" value={ai.narrative_style} />
              )}
              {ai.vocabulary_level && (
                <AIField label="어휘 수준" value={ai.vocabulary_level} />
              )}
              {ai.sentence_structure && (
                <AIField label="문장 구조" value={ai.sentence_structure} />
              )}
              {ai.paragraph_organization && (
                <AIField label="문단 구성" value={ai.paragraph_organization} />
              )}
              {ai.emotional_expression && (
                <AIField label="감정 표현" value={ai.emotional_expression} />
              )}
              {ai.topic_transition && (
                <AIField label="주제 전환" value={ai.topic_transition} />
              )}
              {ai.opening_pattern && (
                <AIField label="글 시작 패턴" value={ai.opening_pattern} />
              )}
              {ai.closing_pattern && (
                <AIField label="글 마무리 패턴" value={ai.closing_pattern} />
              )}
              {ai.reader_engagement && (
                <AIField label="독자 소통 방식" value={ai.reader_engagement} />
              )}
            </div>

            {ai.rhetorical_devices && ai.rhetorical_devices.length > 0 && (
              <>
                <Separator />
                <div>
                  <p className="text-sm font-medium mb-2">수사법</p>
                  <div className="flex flex-wrap gap-2">
                    {ai.rhetorical_devices.map((d, i) => (
                      <Badge key={i} variant="outline">{d}</Badge>
                    ))}
                  </div>
                </div>
              </>
            )}

            {ai.unique_characteristics && ai.unique_characteristics.length > 0 && (
              <>
                <Separator />
                <div>
                  <p className="text-sm font-medium mb-2">독특한 특징</p>
                  <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground">
                    {ai.unique_characteristics.map((c, i) => (
                      <li key={i}>{c}</li>
                    ))}
                  </ul>
                </div>
              </>
            )}

            {ai.content_themes && ai.content_themes.length > 0 && (
              <>
                <Separator />
                <div>
                  <p className="text-sm font-medium mb-2">주요 주제/테마</p>
                  <div className="flex flex-wrap gap-2">
                    {ai.content_themes.map((t, i) => (
                      <Badge key={i}>{t}</Badge>
                    ))}
                  </div>
                </div>
              </>
            )}
          </CardContent>
        </Card>
      )}

      {!analysis && !loading && (
        <Card>
          <CardContent className="pt-6 text-center py-12">
            <p className="text-muted-foreground">
              아직 분석 결과가 없습니다. &quot;분석 실행&quot; 버튼을 클릭하여 시작하세요.
            </p>
            <p className="text-sm text-muted-foreground mt-2">
              먼저 스크래핑 페이지에서 글을 수집해야 합니다.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function StatBox({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-sm text-muted-foreground">{label}</p>
      <p className="text-xl font-semibold mt-0.5">{value}</p>
    </div>
  );
}

function AIField({ label, value }: { label: string; value: string }) {
  return (
    <div className="p-3 bg-muted/50 rounded-lg">
      <p className="text-xs font-medium text-muted-foreground">{label}</p>
      <p className="text-sm mt-1">{value}</p>
    </div>
  );
}
