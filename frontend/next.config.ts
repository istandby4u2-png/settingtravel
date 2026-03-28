import type { NextConfig } from "next";
import path from "node:path";

/**
 * 브라우저가 `/api`로 요청할 때 백엔드로 넘길 주소 (로컬 개발용).
 * `NEXT_PUBLIC_API_URL`이 있으면 프론트가 API를 직접 그 주소로 호출하므로 rewrite는 쓰이지 않습니다.
 */
const backendProxy =
  process.env.BACKEND_PROXY_URL?.replace(/\/$/, "") ?? "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  /** 상위 디렉터리에 다른 lockfile이 있을 때 Vercel/로컬 빌드 경고 완화 */
  outputFileTracingRoot: path.join(process.cwd(), ".."),
  async rewrites() {
    if (process.env.NEXT_PUBLIC_API_URL) {
      return [];
    }
    return [
      {
        source: "/api/:path*",
        destination: `${backendProxy}/api/:path*`,
      },
    ];
  },
  experimental: {
    proxyTimeout: 120_000,
  },
};

export default nextConfig;
