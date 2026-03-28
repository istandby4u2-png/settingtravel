"use client";

import { Suspense, useEffect, useState, useCallback } from "react";
import { useSearchParams } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import { api } from "@/lib/api";

interface PhotoItem {
  id: string;
  filename: string;
  description: string;
  thumbnailUrl: string;
  baseUrl: string;
  creationTime: string;
  width: string;
  height: string;
}

interface EditAnalysis {
  brightness: { current_level?: string; adjustment_factor?: number; description?: string };
  horizon: { is_tilted?: boolean; rotation_degrees?: number; description?: string };
  sky: { has_sky?: boolean; sky_region_top_percent?: number; saturation_boost?: number; description?: string };
  overall_suggestion: string;
}

interface EditResult {
  original_url: string;
  edited_url: string;
  original_filename: string;
  edited_filename: string;
  analysis: EditAnalysis;
  error?: string;
}

function PhotosPageContent() {
  const searchParams = useSearchParams();
  const [authenticated, setAuthenticated] = useState(false);
  const [authChecked, setAuthChecked] = useState(false);
  const [query, setQuery] = useState("");
  const [photos, setPhotos] = useState<PhotoItem[]>([]);
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);

  const [selectedPhoto, setSelectedPhoto] = useState<PhotoItem | null>(null);
  const [editBrightness, setEditBrightness] = useState(true);
  const [editHorizon, setEditHorizon] = useState(true);
  const [editSky, setEditSky] = useState(true);
  const [editing, setEditing] = useState(false);
  const [editResult, setEditResult] = useState<EditResult | null>(null);
  const [editError, setEditError] = useState<string | null>(null);

  const [locationKeywords, setLocationKeywords] = useState<string[]>([]);
  const [extracting, setExtracting] = useState(false);
  const [blogText, setBlogText] = useState("");

  const checkAuth = useCallback(async () => {
    try {
      const data = (await api.getAuthStatus()) as { authenticated: boolean };
      setAuthenticated(data.authenticated);
    } catch {
      setAuthenticated(false);
    } finally {
      setAuthChecked(true);
    }
  }, []);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  useEffect(() => {
    const auth = searchParams.get("auth");
    if (auth === "success") {
      checkAuth();
    }
  }, [searchParams, checkAuth]);

  const handleGoogleLogin = async () => {
    try {
      const data = (await api.getAuthLoginUrl()) as { auth_url?: string; error?: string };
      if (data.error) {
        setSearchError(data.error);
        return;
      }
      if (data.auth_url) {
        window.location.href = data.auth_url;
      }
    } catch (e) {
      setSearchError("Google 로그인 URL을 가져오지 못했습니다.");
    }
  };

  const handleLogout = async () => {
    await api.logoutGoogle();
    setAuthenticated(false);
    setPhotos([]);
    setEditResult(null);
  };

  const handleSearch = async (searchQuery?: string) => {
    const q = searchQuery || query;
    setSearching(true);
    setSearchError(null);
    setPhotos([]);
    try {
      const data = (await api.searchPhotos({ query: q, page_size: 30 })) as {
        photos?: PhotoItem[];
        error?: string;
      };
      if (data.error) {
        setSearchError(data.error);
      } else {
        setPhotos(data.photos || []);
        if ((data.photos || []).length === 0) {
          setSearchError("검색 결과가 없습니다.");
        }
      }
    } catch (e) {
      setSearchError("사진 검색 중 오류가 발생했습니다.");
    } finally {
      setSearching(false);
    }
  };

  const handleExtractLocations = async () => {
    if (!blogText.trim()) return;
    setExtracting(true);
    try {
      const data = (await api.extractLocations(blogText)) as { locations: string[] };
      setLocationKeywords(data.locations || []);
    } catch {
      /* ignore */
    } finally {
      setExtracting(false);
    }
  };

  const handleEdit = async () => {
    if (!selectedPhoto) return;
    setEditing(true);
    setEditError(null);
    setEditResult(null);
    try {
      const data = (await api.editPhoto({
        photo_id: selectedPhoto.id,
        brightness: editBrightness,
        horizon: editHorizon,
        sky: editSky,
      })) as EditResult;
      if (data.error) {
        setEditError(data.error);
      } else {
        setEditResult(data);
      }
    } catch (e) {
      setEditError("사진 편집 중 오류가 발생했습니다.");
    } finally {
      setEditing(false);
    }
  };

  const handleDownload = (filename: string) => {
    window.open(`/api/photos/download/${filename}`, "_blank");
  };

  if (!authChecked) {
    return (
      <div className="p-8 max-w-6xl mx-auto">
        <p className="text-muted-foreground">로딩 중...</p>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">사진 편집</h1>
          <p className="text-muted-foreground mt-1">
            Google Photos에서 장소 사진을 찾아 AI로 편집합니다
          </p>
        </div>
        {authenticated ? (
          <div className="flex items-center gap-3">
            <Badge variant="outline" className="text-green-600 border-green-300">
              Google 연결됨
            </Badge>
            <Button variant="ghost" size="sm" onClick={handleLogout}>
              연결 해제
            </Button>
          </div>
        ) : (
          <Button onClick={handleGoogleLogin} size="lg">
            Google 계정 연결
          </Button>
        )}
      </div>

      {!authenticated && (
        <Card>
          <CardContent className="pt-6">
            <div className="text-center space-y-3 py-8">
              <p className="text-lg font-medium">Google Photos에 연결해주세요</p>
              <p className="text-muted-foreground text-sm max-w-md mx-auto">
                Google 계정을 연결하면 개인 Google Photos에서 여행 사진을 검색하고,
                AI로 편집하여 블로그에 사용할 수 있습니다.
              </p>
              <Button onClick={handleGoogleLogin} size="lg" className="mt-4">
                Google 계정으로 로그인
              </Button>
              <p className="text-xs text-muted-foreground">
                읽기 전용 권한만 요청합니다. 사진이 수정되거나 삭제되지 않습니다.
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {authenticated && (
        <>
          {/* Location extractor */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">장소 키워드 추출</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <p className="text-sm text-muted-foreground">
                생성된 블로그 글을 붙여넣으면 AI가 장소명을 자동으로 추출합니다.
              </p>
              <textarea
                className="w-full min-h-[80px] p-3 rounded-md border border-input bg-background text-sm resize-y"
                placeholder="블로그 글 내용을 붙여넣으세요..."
                value={blogText}
                onChange={(e) => setBlogText(e.target.value)}
              />
              <div className="flex items-center gap-3">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleExtractLocations}
                  disabled={extracting || !blogText.trim()}
                >
                  {extracting ? "추출 중..." : "장소 추출"}
                </Button>
                {locationKeywords.length > 0 && (
                  <div className="flex flex-wrap gap-1.5">
                    {locationKeywords.map((loc, i) => (
                      <Badge
                        key={i}
                        variant="secondary"
                        className="cursor-pointer hover:bg-primary hover:text-primary-foreground transition-colors"
                        onClick={() => {
                          setQuery(loc);
                          handleSearch(loc);
                        }}
                      >
                        {loc}
                      </Badge>
                    ))}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Search */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">사진 검색</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-2">
                <Input
                  placeholder="장소명으로 검색 (예: 교토, 마쓰야마...)"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") handleSearch();
                  }}
                  className="flex-1"
                />
                <Button onClick={() => handleSearch()} disabled={searching}>
                  {searching ? "검색 중..." : "검색"}
                </Button>
              </div>

              {searchError && (
                <p className="text-sm text-destructive">{searchError}</p>
              )}

              {photos.length > 0 && (
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
                  {photos.map((photo) => (
                    <div
                      key={photo.id}
                      className={`relative rounded-lg overflow-hidden border-2 cursor-pointer transition-all hover:shadow-md ${
                        selectedPhoto?.id === photo.id
                          ? "border-primary ring-2 ring-primary/30"
                          : "border-border"
                      }`}
                      onClick={() => setSelectedPhoto(photo)}
                    >
                      <img
                        src={photo.thumbnailUrl}
                        alt={photo.filename}
                        className="w-full aspect-[4/3] object-cover"
                        loading="lazy"
                      />
                      <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/60 to-transparent p-2">
                        <p className="text-white text-xs truncate">
                          {photo.filename}
                        </p>
                        {photo.creationTime && (
                          <p className="text-white/70 text-[10px]">
                            {new Date(photo.creationTime).toLocaleDateString("ko-KR")}
                          </p>
                        )}
                      </div>
                      {selectedPhoto?.id === photo.id && (
                        <div className="absolute top-2 right-2">
                          <div className="w-6 h-6 bg-primary rounded-full flex items-center justify-center text-primary-foreground text-xs font-bold">
                            ✓
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Edit panel */}
          {selectedPhoto && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">
                  AI 사진 편집 - {selectedPhoto.filename}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex flex-wrap gap-4">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={editBrightness}
                      onChange={(e) => setEditBrightness(e.target.checked)}
                      className="rounded border-input"
                    />
                    <span className="text-sm">밝기 자동 조정</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={editHorizon}
                      onChange={(e) => setEditHorizon(e.target.checked)}
                      className="rounded border-input"
                    />
                    <span className="text-sm">수평 보정</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={editSky}
                      onChange={(e) => setEditSky(e.target.checked)}
                      className="rounded border-input"
                    />
                    <span className="text-sm">하늘 파랗게</span>
                  </label>
                </div>

                <Button
                  onClick={handleEdit}
                  disabled={editing}
                  className="w-full"
                  size="lg"
                >
                  {editing ? "AI가 사진을 편집하고 있습니다..." : "AI 편집 실행"}
                </Button>

                {editError && (
                  <p className="text-sm text-destructive">{editError}</p>
                )}

                {editing && (
                  <div className="flex items-center gap-3 py-4">
                    <div className="h-2 w-2 rounded-full bg-primary animate-pulse" />
                    <span className="text-sm text-muted-foreground">
                      Gemini Vision이 사진을 분석하고 편집 중입니다...
                    </span>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Edit result */}
          {editResult && (
            <Card>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <CardTitle className="text-base">편집 결과</CardTitle>
                  <Button
                    onClick={() => handleDownload(editResult.edited_filename)}
                    size="sm"
                  >
                    편집본 다운로드
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Before/After comparison */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label className="text-sm font-medium">원본</Label>
                    <div className="rounded-lg overflow-hidden border border-border">
                      <img
                        src={editResult.original_url}
                        alt="원본"
                        className="w-full"
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label className="text-sm font-medium">편집 후</Label>
                    <div className="rounded-lg overflow-hidden border border-primary/50">
                      <img
                        src={editResult.edited_url}
                        alt="편집 후"
                        className="w-full"
                      />
                    </div>
                  </div>
                </div>

                <Separator />

                {/* AI analysis details */}
                <div className="space-y-3">
                  <p className="text-sm font-medium">AI 분석 결과</p>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    {editResult.analysis.brightness?.description && (
                      <div className="p-3 rounded-lg bg-accent/50 space-y-1">
                        <p className="text-xs font-medium text-muted-foreground">밝기</p>
                        <p className="text-sm">{editResult.analysis.brightness.description}</p>
                        {editResult.analysis.brightness.adjustment_factor && (
                          <Badge variant="outline" className="text-xs">
                            x{editResult.analysis.brightness.adjustment_factor}
                          </Badge>
                        )}
                      </div>
                    )}
                    {editResult.analysis.horizon?.description && (
                      <div className="p-3 rounded-lg bg-accent/50 space-y-1">
                        <p className="text-xs font-medium text-muted-foreground">수평</p>
                        <p className="text-sm">{editResult.analysis.horizon.description}</p>
                        {editResult.analysis.horizon.rotation_degrees !== undefined && editResult.analysis.horizon.rotation_degrees !== 0 && (
                          <Badge variant="outline" className="text-xs">
                            {editResult.analysis.horizon.rotation_degrees > 0 ? "+" : ""}
                            {editResult.analysis.horizon.rotation_degrees}°
                          </Badge>
                        )}
                      </div>
                    )}
                    {editResult.analysis.sky?.description && (
                      <div className="p-3 rounded-lg bg-accent/50 space-y-1">
                        <p className="text-xs font-medium text-muted-foreground">하늘</p>
                        <p className="text-sm">{editResult.analysis.sky.description}</p>
                        {editResult.analysis.sky.has_sky && (
                          <Badge variant="outline" className="text-xs">
                            상단 {editResult.analysis.sky.sky_region_top_percent}%
                          </Badge>
                        )}
                      </div>
                    )}
                  </div>
                  {editResult.analysis.overall_suggestion && (
                    <p className="text-sm text-muted-foreground italic">
                      {editResult.analysis.overall_suggestion}
                    </p>
                  )}
                </div>

                <div className="flex gap-2 pt-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleDownload(editResult.original_filename)}
                  >
                    원본 다운로드
                  </Button>
                  <Button
                    size="sm"
                    onClick={() => handleDownload(editResult.edited_filename)}
                  >
                    편집본 다운로드
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );
}

export default function PhotosPage() {
  return (
    <Suspense
      fallback={
        <div className="p-8 max-w-6xl mx-auto space-y-4">
          <div className="h-8 w-48 rounded-md bg-muted animate-pulse" />
          <div className="h-64 rounded-lg bg-muted animate-pulse" />
        </div>
      }
    >
      <PhotosPageContent />
    </Suspense>
  );
}
