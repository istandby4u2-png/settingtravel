import asyncio
import httpx
from bs4 import BeautifulSoup

BRUNCH_BASE = "https://brunch.co.kr"
AUTHOR_ID = "istandby4u2"

_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

MAX_ARTICLE_NO = 300
CONSECUTIVE_404_LIMIT = 15


async def _discover_article_numbers(client: httpx.AsyncClient) -> list[int]:
    """1번부터 순차 HEAD 요청으로 존재하는 글 번호를 수집합니다."""
    found: list[int] = []
    consecutive_404 = 0

    for no in range(1, MAX_ARTICLE_NO + 1):
        url = f"{BRUNCH_BASE}/@{AUTHOR_ID}/{no}"
        try:
            resp = await client.head(url)
            if resp.status_code == 200:
                found.append(no)
                consecutive_404 = 0
            else:
                consecutive_404 += 1
        except Exception:
            consecutive_404 += 1

        if consecutive_404 >= CONSECUTIVE_404_LIMIT:
            break
        await asyncio.sleep(0.1)

    print(f"[brunch] Discovered {len(found)} articles (scanned up to {no})")
    return found


async def _scrape_article(
    client: httpx.AsyncClient, no: int, index: int, total: int,
) -> dict | None:
    url = f"{BRUNCH_BASE}/@{AUTHOR_ID}/{no}"
    print(f"[brunch] {index}/{total}: {url}")
    try:
        resp = await client.get(url)
        if resp.status_code != 200:
            print(f"[brunch] HTTP {resp.status_code} for {url}")
            return None
    except Exception as e:
        print(f"[brunch] Error: {url}: {e}")
        return None

    soup = BeautifulSoup(resp.text, "html.parser")

    title_el = soup.select_one("meta[property='og:title']") or soup.select_one("h1.cover_title")
    title = (
        title_el.get("content") if title_el and title_el.name == "meta"
        else title_el.get_text(strip=True) if title_el else ""
    )

    body_el = (
        soup.select_one(".wrap_body")
        or soup.select_one("div.wrap_body_frame")
        or soup.select_one("article")
        or soup.select_one(".article_view")
    )
    content = body_el.get_text("\n", strip=True) if body_el else ""

    if not content:
        desc_el = soup.select_one("meta[property='og:description']")
        if desc_el:
            content = desc_el.get("content", "")

    date_el = (
        soup.select_one("meta[property='article:published_time']")
        or soup.select_one(".publish_time")
        or soup.select_one(".date_info")
    )
    pub_date = (
        date_el.get("content") if date_el and date_el.name == "meta"
        else date_el.get_text(strip=True) if date_el else ""
    )

    og_img = soup.select_one("meta[property='og:image']")
    thumbnail = og_img.get("content", "").strip() if og_img else ""

    images: list[str] = []
    body_root = body_el or soup
    for img in body_root.select("img[src]"):
        src = (img.get("data-src") or img.get("src") or "").strip()
        if src and src not in images and not src.endswith(".gif"):
            images.append(src)

    if not content or len(content) < 30:
        print(f"[brunch] Skipping (too short): {url}")
        return None

    print(f"[brunch] OK: '{title[:40]}' ({len(content)} chars, {len(images)} imgs)")
    return {
        "source": "brunch",
        "title": title,
        "content": content,
        "url": url,
        "published_date": pub_date,
        "thumbnail": thumbnail,
        "images": images,
    }


async def scrape_brunch() -> list[dict]:
    """브런치 블로그의 모든 글을 수집합니다 (Playwright 불필요)."""
    results: list[dict] = []

    async with httpx.AsyncClient(
        headers={"User-Agent": _UA},
        follow_redirects=True,
        timeout=20,
    ) as client:
        numbers = await _discover_article_numbers(client)
        if not numbers:
            print("[brunch] No articles found")
            return []

        print(f"[brunch] Scraping {len(numbers)} articles...")
        for i, no in enumerate(numbers, 1):
            article = await _scrape_article(client, no, i, len(numbers))
            if article:
                results.append(article)
            await asyncio.sleep(0.3)

    print(f"[brunch] Scraping complete: {len(results)} articles collected")
    return results
