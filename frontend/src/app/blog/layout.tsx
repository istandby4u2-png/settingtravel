import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "다정한 여행의 배경 | 배경여행",
  description:
    "책·영화·드라마 속 여행지와 이야기. 브런치·네이버에서 옮겨 온 글 모음입니다.",
};

export default function BlogLayout({ children }: { children: React.ReactNode }) {
  return children;
}
