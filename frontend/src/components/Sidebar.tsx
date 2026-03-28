"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  { href: "/", label: "home", icon: "🌐" },
  { href: "/dashboard", label: "대시보드", icon: "📊" },
  { href: "/scrape", label: "스크래핑", icon: "🔍" },
  { href: "/analysis", label: "문체 분석", icon: "📝" },
  { href: "/generate", label: "글 생성", icon: "✨" },
  { href: "/photos", label: "사진 편집", icon: "📷" },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 min-h-screen border-r border-border bg-card flex flex-col">
      <div className="p-6 border-b border-border">
        <h1 className="text-xl font-bold tracking-tight">배경여행</h1>
        <p className="text-sm text-muted-foreground mt-1">
          블로그 문체 분석 &amp; 자동 생성
        </p>
      </div>
      <nav className="flex-1 p-4 space-y-1">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:text-foreground hover:bg-accent"
              }`}
            >
              <span className="text-base">{item.icon}</span>
              {item.label}
            </Link>
          );
        })}
      </nav>
      <div className="p-4 border-t border-border">
        <p className="text-xs text-muted-foreground">
          Powered by Gemini AI
        </p>
      </div>
    </aside>
  );
}
