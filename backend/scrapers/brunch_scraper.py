import asyncio
import re
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup


BRUNCH_BASE = "https://brunch.co.kr"
AUTHOR_URL = f"{BRUNCH_BASE}/@istandby4u2"


async def _get_article_urls(page) -> list[str]:
    """Load the author page and collect article URLs."""
    print("[brunch] Loading author page...")
    await page.goto(AUTHOR_URL, wait_until="domcontentloaded", timeout=20000)
    await asyncio.sleep(3)

    # Scroll a few times to load more articles
    for i in range(15):
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(1.5)
        # Try clicking "더보기" button
        try:
            more_btn = page.locator("a.btn_more, button.btn_more, .wrap_btn_more a, button:has-text('더보기')")
            if await more_btn.count() > 0 and await more_btn.first.is_visible():
                await more_btn.first.click()
                await asyncio.sleep(2)
        except Exception:
            pass

    html = await page.content()
    soup = BeautifulSoup(html, "html.parser")

    urls: list[str] = []
    for a_tag in soup.select("a[href]"):
        href = a_tag.get("href", "")
        # Match /@istandby4u2/{number} pattern
        if re.match(r'^/@istandby4u2/\d+$', href):
            full = BRUNCH_BASE + href
            if full not in urls:
                urls.append(full)

    print(f"[brunch] Found {len(urls)} article URLs")
    return urls


async def _scrape_article(page, url: str, index: int, total: int) -> dict | None:
    """Scrape a single brunch article."""
    print(f"[brunch] Scraping article {index}/{total}: {url}")
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
        await asyncio.sleep(2)
        html = await page.content()
    except Exception as e:
        print(f"[brunch] Failed to load {url}: {e}")
        return None

    soup = BeautifulSoup(html, "html.parser")

    # Title
    title_el = (
        soup.select_one("h1.cover_title")
        or soup.select_one("meta[property='og:title']")
    )
    if title_el:
        title = title_el.get_text(strip=True) if title_el.name != "meta" else title_el.get("content", "")
    else:
        title = ""

    # Body
    body_el = (
        soup.select_one(".wrap_body")
        or soup.select_one("div.wrap_body_frame")
        or soup.select_one("article")
        or soup.select_one(".article_view")
    )
    content = body_el.get_text("\n", strip=True) if body_el else ""

    # Date
    date_el = (
        soup.select_one(".publish_time")
        or soup.select_one("meta[property='article:published_time']")
        or soup.select_one(".date_info")
    )
    if date_el:
        pub_date = date_el.get_text(strip=True) if date_el.name != "meta" else date_el.get("content", "")
    else:
        pub_date = ""

    if not content or len(content) < 30:
        print(f"[brunch] Skipping (content too short): {url}")
        return None

    print(f"[brunch] OK: '{title[:40]}' ({len(content)} chars)")
    return {
        "source": "brunch",
        "title": title,
        "content": content,
        "url": url,
        "published_date": pub_date,
    }


async def scrape_brunch() -> list[dict]:
    """Scrape all articles from the brunch blog."""
    results: list[dict] = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        )
        page = await context.new_page()

        urls = await _get_article_urls(page)

        for i, url in enumerate(urls, 1):
            article = await _scrape_article(page, url, i, len(urls))
            if article:
                results.append(article)
            await asyncio.sleep(1)

        await browser.close()

    print(f"[brunch] Scraping complete: {len(results)} articles collected")
    return results
