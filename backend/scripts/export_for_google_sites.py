#!/usr/bin/env python3
"""SQLite posts → Markdown 파일 + 원문 링크 HTML (Google Sites Essay 작업용)."""

import json
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "blog_service.db"
OUT = ROOT.parent / "exports" / "essay_for_google_sites"


def safe_name(title: str, post_id: int, source: str) -> str:
    base = (title or "").strip() or f"post_{post_id}"
    base = re.sub(r'[<>:"/\\|?*\n\r\t]', "_", base)[:90].strip(" ._") or f"{source}_{post_id}"
    return f"{post_id:04d}_{source}_{base}"


def main() -> None:
    if not DB.is_file():
        raise SystemExit(f"DB 없음: {DB}")

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT id, source, title, content, url, published_date
        FROM posts
        ORDER BY source, id
        """
    ).fetchall()
    conn.close()

    md_dir = OUT / "markdown"
    md_dir.mkdir(parents=True, exist_ok=True)

    manifest: list[dict] = []
    brunch_links: list[tuple[str, str]] = []
    naver_links: list[tuple[str, str]] = []

    for r in rows:
        name = safe_name(r["title"], r["id"], r["source"])
        md_path = md_dir / f"{name}.md"
        header = (
            f"# {r['title']}\n\n"
            f"- 출처: **{r['source']}**\n"
            f"- 원문: {r['url']}\n"
            f"- 게시일: {r['published_date'] or '—'}\n\n"
            "---\n\n"
        )
        md_path.write_text(header + (r["content"] or ""), encoding="utf-8")

        title = r["title"] or "(제목 없음)"
        manifest.append(
            {
                "id": r["id"],
                "source": r["source"],
                "title": title,
                "url": r["url"],
                "published_date": r["published_date"],
                "markdown_file": str(md_path.relative_to(OUT)),
            }
        )
        pair = (title, r["url"])
        if r["source"] == "brunch":
            brunch_links.append(pair)
        else:
            naver_links.append(pair)

    (OUT / "manifest.json").write_text(
        json.dumps({"count": len(manifest), "posts": manifest}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # Google Sites > 삽입 > 임베드 에 붙여 넣을 수 있는 단순 링크 목록 HTML
    def block(title: str, links: list[tuple[str, str]]) -> str:
        lis = "".join(
            f'<li><a href="{url}" target="_blank" rel="noopener">{title}</a></li>\n'
            for title, url in links
        )
        return f"<section><h2>{title}</h2>\n<ul>\n{lis}</ul></section>\n"

    html = (
        "<!DOCTYPE html><html><head><meta charset='utf-8'><title>Essay 링크 목록</title></head>"
        "<body>\n"
        f"<h1>Essay — 원문 링크 ({len(rows)}개)</h1>\n"
        "<p>Google Sites: 삽입 → 임베드 → 코드 삽입 시도 (길이 제한 있으면 섹션 나누기)</p>\n"
        + block("Brunch", brunch_links)
        + block("네이버 블로그", naver_links)
        + "</body></html>"
    )
    (OUT / "links_embed.html").write_text(html, encoding="utf-8")

    print(f"완료: {len(rows)}개 → {OUT}")
    print(f"  - markdown/*.md")
    print(f"  - manifest.json")
    print(f"  - links_embed.html")


if __name__ == "__main__":
    main()
