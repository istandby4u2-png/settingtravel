/** 공개 사이트의 절대 URL (OG·canonical). 배포 시 `NEXT_PUBLIC_SITE_URL`을 설정하세요. */
export function getSiteUrl(): URL {
  const fromEnv = process.env.NEXT_PUBLIC_SITE_URL?.trim();
  if (fromEnv) {
    try {
      const normalized = fromEnv.replace(/\/$/, "");
      return new URL(normalized);
    } catch {
      // ignore invalid env
    }
  }
  if (process.env.VERCEL_URL) {
    return new URL(`https://${process.env.VERCEL_URL}`);
  }
  return new URL("http://localhost:3000");
}
