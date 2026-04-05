import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      { hostname: "**.kakaocdn.net" },
      { hostname: "**.daumcdn.net" },
      { hostname: "**.pstatic.net" },
      { hostname: "**.blogpay.co.kr" },
      { hostname: "postfiles.pstatic.net" },
      { hostname: "t1.daumcdn.net" },
    ],
  },
  async rewrites() {
    if (process.env.NEXT_PUBLIC_API_URL) {
      return [];
    }
    const backendProxy =
      process.env.BACKEND_PROXY_URL?.replace(/\/$/, "") ?? "http://127.0.0.1:8000";
    return [
      {
        source: "/api/:path*",
        destination: `${backendProxy}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
