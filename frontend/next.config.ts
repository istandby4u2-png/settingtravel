import type { NextConfig } from "next";

const backendProxy =
  process.env.BACKEND_PROXY_URL?.replace(/\/$/, "") ?? "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
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
};

export default nextConfig;
