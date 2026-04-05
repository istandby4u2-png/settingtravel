import asyncio
import re
import httpx
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

BRUNCH_BASE = "https://brunch.co.kr"
AUTHOR_ID = "istandby4u2"
AUTHOR_URL = f"{BRUNCH_BASE}/@{AUTHOR_ID}"

_CHROMIUM_ARGS = [
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--single-process",
]

_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


# ── URL 수집 ────────────────────────────────────────────

async def _get_urls_via_api() -> list[str]:
    """brunch API로 글 목록 가져오기 (Playwright 불필요)."""
    urls: list[str] = []
    print("[brunch] Trying API method...")
    async with httpx.AsyncClient(
        headers={"User-Agent": _UA},
        follow_redirects=True,
        timeout=20,
    ) as client:
        page_num = 1
        while True:
            api_url = (
                f"{BRUNCH_BASE}/api/v1/magazine/@{AUTHOR_ID}/article"
                f"?page={page_num}&size=20"
            )
            try:
                resp = await client.get(api_url)
                if resp.status_code != 200:
                    print(f"[brunch] API status {resp.status_code}, stopping")
                    break
                data = resp.json()
            except Exception as e:
                print(f"[brunch] API error: {e}")
                break

            articles = data.get("data", data.get("list", []))
            if isinstance(data, list):
                articles = data
            if not articles:
                break

            for item in articles:
                no = item.get("no") or item.get("articleNo")
                if no:
                    urls.append(f"{BRUNCH_BASE}/@{AUTHOR_ID}/{no}")
            print(f"[brunch] API page {page_num}: {len(articles)} items (total {len(urls)})")

            if len(articles) < 20:
                break
            page_num += 1
            await asyncio.sleep(0.5)

    return urls


async def _get_urls_via_rss() -> list[str]:
    """RSS 피드에서 글 URL 가져오기."""
    urls: list[str] = []
    print("[brunch] Trying RSS method...")
    async with httpx.AsyncClient(
        headers={"User-Agent": _UA},
        follow_redirects=True,
        timeout=15,
    ) as client:
        try:
            resp = await client.get(f"{BRUNCH_BASE}/rss/@@{AUTHOR_ID}")
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                for item in soup.select("item"):
                    link_el = item.select_one("link")
                    if link_el:
                        link_text = (link_el.get_text(strip=True) or (link_el.next_sibling or "")).strip()
                        if link_text and f"@{AUTHOR_ID}/" in link_text:
                            if link_text not in urls:
                                urls.append(link_text)
                print(f"[brunch] RSS found {len(urls)} URLs")
        except Exception as e:
            print(f"[brunch] RSS error: {e}")
    return urls


async def _get_urls_via_playwright() -> list[str]:
    """Playwright 폴백 — API/RSS 모두 실패할 때만."""
    urls: list[str] = []
    print("[brunch] Falling back to Playwright for URL list...")
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True, args=_CHROMIUM_ARGS, timeout=30_000,
            )
            context = await browser.new_context(user_agent=_UA)
            page = await context.new_page()

            await page.goto(AUTHOR_URL, wait_until="domcontentloaded", timeout=20_000)
            await asyncio.sleep(3)

            for _ in range(15):
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(1.5)
                try:
                    more_btn = page.locator(
                        "a.btn_more, button.btn_more, .wrap_btn_more a, button:has-text('더보기')"
                    )
                    if await more_btn.count() > 0 and await more_btn.first.is_visible():
                        await more_btn.first.click()
                        await asyncio.sleep(2)
                except Exception:
                    pass

            html = await page.content()
            soup = BeautifulSoup(html, "html.parser")
            for a_tag in soup.select("a[href]"):
                href = a_tag.get("href", "")
                if re.match(rf'^/@{AUTHOR_ID}/\d+$', href):
                    full = BRUNCH_BASE + href
                    if full not in urls:
                        urls.append(full)

            await browser.close()
    except Exception as e:
        print(f"[brunch] Playwright URL fetch failed: {e}")

    print(f"[brunch] Playwright found {len(urls)} URLs")
    return urls


# ── 개별 글 스크래핑 ─────────────────────────────────────

async def _scrape_article_httpx(
    client: httpx.AsyncClient, url: str, index: int, total: int,
) -> dict | None:
    """httpx로 개별 글 스크래핑 (JS 렌더링 불필요한 메타+본문 추출)."""
    print(f"[brunch] httpx {index}/{total}: {url}")
    try:
        resp = await client.get(url)
        if resp.status_code != 200:
            print(f"[brunch] HTTP {resp.status_code} for {url}")
            return None
    except Exception as e:
        print(f"[brunch] Error fetching {url}: {e}")
        return None

    soup = BeautifulSoup(resp.text, "html.parser")

    title_el = soup.select_one("meta[property='og:title']") or soup.select_one("h1.cover_title")
    title = (title_el.get("content") if title_el and title_el.name == "meta"
             else title_el.get_text(strip=True) if title_el else "")

    body_el = (
        soup.select_one(".wrap_body")
        or soup.select_one("div.wrap_body_frame")
        or soup.select_one("article")
        or soup.select_one(".article_view")
    )
    content = body_el.get_text("\n", strip=True) if body_el else ""

    desc_el = soup.select_one("meta[property='og:description']")
    if not content and desc_el:
        content = desc_el.get("content", "")

    date_el = (
        soup.select_one("meta[property='article:published_time']")
        or soup.select_one(".publish_time")
        or soup.select_one(".date_info")
    )
    pub_date = (date_el.get("content") if date_el and date_el.name == "meta"
                else date_el.get_text(strip=True) if date_el else "")

    if not content or len(content) < 30:
        print(f"[brunch] Skipping (too short): {url}")
        return None

    print(f"[brunch] OK: '{title[:40]}' ({len(content)} chars)")
    return {"source": "brunch", "title": title, "content": content, "url": url, "published_date": pub_date}


async def _scrape_article_playwright(page, url: str, index: int, total: int) -> dict | None:
    """Playwright 폴백 — httpx로 본문을 못 가져온 경우."""
    print(f"[brunch] Playwright retry {index}/{total}: {url}")
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=20_000)
        await asyncio.sleep(2)
        html = await page.content()
    except Exception as e:
        print(f"[brunch] Playwright failed {url}: {e}")
        return None

    soup = BeautifulSoup(html, "html.parser")
    title_el = soup.select_one("h1.cover_title") or soup.select_one("meta[property='og:title']")
    title = (title_el.get_text(strip=True) if title_el and title_el.name != "meta"
             else title_el.get("content", "") if title_el else "")
    body_el = (
        soup.select_one(".wrap_body") or soup.select_one("div.wrap_body_frame")
        or soup.select_one("article") or soup.select_one(".article_view")
    )
    content = body_el.get_text("\n", strip=True) if body_el else ""
    date_el = (
        soup.select_one(".publish_time") or soup.select_one("meta[property='article:published_time']")
        or soup.select_one(".date_info")
    )
    pub_date = (date_el.get_text(strip=True) if date_el and date_el.name != "meta"
                else date_el.get("content", "") if date_el else "")

    if not content or len(content) < 30:
        return None

    print(f"[brunch] PW OK: '{title[:40]}' ({len(content)} chars)")
    return {"source": "brunch", "title": title, "content": content, "url": url, "published_date": pub_date}


# ── 메인 ─────────────────────────────────────────────────

async def scrape_brunch() -> list[dict]:
    """브런치 블로그의 모든 글을 수집합니다."""

    urls = await _get_urls_via_api()
    if not urls:
        urls = await _get_urls_via_rss()
    if not urls:
        urls = await _get_urls_via_playwright()
    if not urls:
        print("[brunch] Could not find any article URLs")
        return []

    print(f"[brunch] Total {len(urls)} articles to scrape")
    results: list[dict] = []
    failed_urls: list[tuple[int, str]] = []

    async with httpx.AsyncClient(
        headers={"User-Agent": _UA}, follow_redirects=True, timeout=20,
    ) as client:
        for i, url in enumerate(urls, 1):
            article = await _scrape_article_httpx(client, url, i, len(urls))
            if article:
                results.append(article)
            else:
                failed_urls.append((i, url))
            await asyncio.sleep(0.5)

    if failed_urls:
        print(f"[brunch] Retrying {len(failed_urls)} failed articles with Playwright...")
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True, args=_CHROMIUM_ARGS, timeout=30_000,
                )
                context = await browser.new_context(user_agent=_UA)
                page = await context.new_page()

                for idx, url in failed_urls:
                    article = await _scrape_article_playwright(page, url, idx, len(urls))
                    if article:
                        results.append(article)
                    await asyncio.sleep(1)

                await browser.close()
        except Exception as e:
            print(f"[brunch] Playwright retry phase failed: {e}")

    print(f"[brunch] Scraping complete: {len(results)} articles collected")
    return results
