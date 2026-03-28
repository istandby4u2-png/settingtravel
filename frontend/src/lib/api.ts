const API_BASE =
  typeof process.env.NEXT_PUBLIC_API_URL === "string" && process.env.NEXT_PUBLIC_API_URL.length > 0
    ? `${process.env.NEXT_PUBLIC_API_URL.replace(/\/$/, "")}/api`
    : "/api";

async function fetchAPI<T = unknown>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });

  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }

  return res.json();
}

export const api = {
  // Scraping
  getScrapeStatus: () => fetchAPI("/scrape/status"),
  startScraping: () => fetchAPI("/scrape/start", { method: "POST" }),
  getPosts: (source?: string, page = 1) =>
    fetchAPI(`/scrape/posts?page=${page}${source ? `&source=${source}` : ""}`),
  getPostDetail: (id: number) => fetchAPI(`/scrape/posts/${id}`),
  /** format=json: JSON. format=markdown: ZIP of .md files */
  getExportUrl: (format: "json" | "markdown" = "json", source?: "brunch" | "naver") => {
    const q = new URLSearchParams({ format });
    if (source) q.set("source", source);
    return `${API_BASE}/scrape/export?${q.toString()}`;
  },

  // Public blog (수집 글)
  getBlogPosts: (source?: "brunch" | "naver", page = 1, limit = 12) =>
    fetchAPI<{
      posts: Array<{
        id: number;
        source: string;
        title: string;
        excerpt: string;
        url: string;
        published_date: string | null;
        scraped_at: string | null;
      }>;
      total: number;
      page: number;
      limit: number;
    }>(`/blog/posts?page=${page}&limit=${limit}${source ? `&source=${source}` : ""}`),

  getBlogPost: async (id: number) => {
    const res = await fetch(`${API_BASE}/blog/posts/${id}`, {
      headers: { "Content-Type": "application/json" },
    });
    if (res.status === 404) return null;
    if (!res.ok) throw new Error(`API error: ${res.status} ${res.statusText}`);
    return res.json() as Promise<{
      id: number;
      source: string;
      title: string;
      content: string;
      url: string;
      published_date: string | null;
      scraped_at: string | null;
    }>;
  },

  // Analysis
  runAnalysis: () => fetchAPI("/analyze/run", { method: "POST" }),
  getLatestAnalysis: () => fetchAPI("/analyze/latest"),
  getAnalysisHistory: () => fetchAPI("/analyze/history"),
  runStatisticalOnly: () => fetchAPI("/analyze/statistical-only", { method: "POST" }),

  // Generation
  generatePost: (data: { topic: string; length: string; additional_instructions: string; reference_url?: string }) =>
    fetchAPI("/generate/create", { method: "POST", body: JSON.stringify(data) }),
  getGenerationHistory: (page = 1) => fetchAPI(`/generate/history?page=${page}`),
  getGeneratedPost: (id: number) => fetchAPI(`/generate/history/${id}`),

  // Photos
  getAuthStatus: () => fetchAPI("/auth/google/status"),
  getAuthLoginUrl: () => fetchAPI("/auth/google/login"),
  logoutGoogle: () => fetchAPI("/auth/google/logout", { method: "POST" }),
  searchPhotos: (data: { query: string; page_size?: number; page_token?: string | null }) =>
    fetchAPI("/photos/search", { method: "POST", body: JSON.stringify(data) }),
  editPhoto: (data: { photo_id: string; brightness?: boolean; horizon?: boolean; sky?: boolean }) =>
    fetchAPI("/photos/edit", { method: "POST", body: JSON.stringify(data) }),
  extractLocations: (text: string) =>
    fetchAPI("/photos/extract-locations", { method: "POST", body: JSON.stringify({ text }) }),

  // Booklog
  getBooklogYears: () =>
    fetchAPI<{ years: number[]; has_unassigned: boolean }>("/booklog/years"),
  getBooklogItems: (opts?: { year?: number; unassigned?: boolean; page?: number; limit?: number }) => {
    const q = new URLSearchParams();
    if (opts?.year !== undefined) q.set("year", String(opts.year));
    if (opts?.unassigned) q.set("unassigned", "true");
    if (opts?.page) q.set("page", String(opts.page));
    if (opts?.limit) q.set("limit", String(opts.limit));
    const qs = q.toString();
    return fetchAPI<{
      items: Array<{
        id: number;
        year: number | null;
        title: string;
        author: string | null;
        note: string | null;
        source_url: string | null;
      }>;
      total: number;
      page: number;
      limit: number;
    }>(`/booklog/items${qs ? `?${qs}` : ""}`);
  },

  // Health
  health: () => fetchAPI("/health"),
};
