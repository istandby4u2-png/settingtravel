import asyncio
import re
import httpx
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright


BLOG_ID = "istandby4u2"
MOBILE_BASE = f"https://m.blog.naver.com/{BLOG_ID}"


async def _get_post_urls_via_api() -> list[str]:
    """Use Naver blog's internal API to fetch post list."""
    urls: list[str] = []
    page_num = 1

    print("[naver] Trying API method to get post list...")
    async with httpx.AsyncClient(
        headers={
            "User-Agent": (
                "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) "
                "Version/16.0 Mobile/15E148 Safari/604.1"
            ),
            "Referer": f"https://m.blog.naver.com/{BLOG_ID}",
        },
        follow_redirects=True,
        timeout=20,
    ) as client:
        while True:
            api_url = (
                f"https://m.blog.naver.com/api/blogs/{BLOG_ID}/post-list"
                f"?categoryNo=0&itemCount=30&page={page_num}"
            )
            try:
                resp = await client.get(api_url)
                if resp.status_code != 200:
                    print(f"[naver] API returned {resp.status_code}, stopping")
                    break
                data = resp.json()
            except Exception as e:
                print(f"[naver] API error: {e}")
                break

            items = data.get("result", {}).get("items", [])
            if not items:
                print(f"[naver] No more items at page {page_num}")
                break

            for item in items:
                log_no = item.get("logNo")
                if log_no:
                    urls.append(f"https://m.blog.naver.com/{BLOG_ID}/{log_no}")

            print(f"[naver] API page {page_num}: got {len(items)} items (total: {len(urls)})")

            has_next = data.get("result", {}).get("hasNext", False)
            if not has_next:
                break
            page_num += 1
            await asyncio.sleep(0.5)

    return urls


async def _get_post_urls_via_playwright() -> list[str]:
    """Fallback: use Playwright to scrape the post list from mobile page."""
    urls: list[str] = []
    print("[naver] Falling back to Playwright method...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu", "--single-process"],
            timeout=30_000,
        )
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) "
                "Version/16.0 Mobile/15E148 Safari/604.1"
            )
        )
        page = await context.new_page()

        desktop_url = f"https://blog.naver.com/PostList.naver?blogId={BLOG_ID}&categoryNo=0&from=postList"
        print(f"[naver] Loading {desktop_url}")
        await page.goto(desktop_url, wait_until="domcontentloaded", timeout=20000)
        await asyncio.sleep(3)

        # Get the iframe content
        frames = page.frames
        for frame in frames:
            html = await frame.content()
            soup = BeautifulSoup(html, "html.parser")
            for a_tag in soup.select(f'a[href]'):
                href = a_tag.get("href", "")
                match = re.search(rf'{BLOG_ID}/(\d+)', href)
                if match:
                    full_url = f"https://m.blog.naver.com/{BLOG_ID}/{match.group(1)}"
                    if full_url not in urls:
                        urls.append(full_url)

        print(f"[naver] Playwright found {len(urls)} post URLs")
        await browser.close()

    return urls


async def _get_post_urls_via_rss() -> list[str]:
    """Try RSS feed to get post URLs."""
    urls: list[str] = []
    print("[naver] Trying RSS method...")

    async with httpx.AsyncClient(
        headers={"User-Agent": "Mozilla/5.0"},
        follow_redirects=True,
        timeout=15,
    ) as client:
        rss_url = f"https://rss.blog.naver.com/{BLOG_ID}.xml"
        try:
            resp = await client.get(rss_url)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                for item in soup.select("item"):
                    link_el = item.select_one("link")
                    if link_el:
                        link_text = link_el.get_text(strip=True) or link_el.next_sibling
                        if link_text and isinstance(link_text, str):
                            link_text = link_text.strip()
                            match = re.search(rf'{BLOG_ID}/(\d+)', link_text)
                            if match:
                                mobile_url = f"https://m.blog.naver.com/{BLOG_ID}/{match.group(1)}"
                                if mobile_url not in urls:
                                    urls.append(mobile_url)
                print(f"[naver] RSS found {len(urls)} post URLs")
        except Exception as e:
            print(f"[naver] RSS error: {e}")

    return urls


async def _scrape_post(client: httpx.AsyncClient, url: str, index: int, total: int) -> dict | None:
    """Scrape a single Naver blog post using the mobile URL."""
    print(f"[naver] Scraping post {index}/{total}: {url}")
    try:
        resp = await client.get(url)
        if resp.status_code != 200:
            print(f"[naver] HTTP {resp.status_code} for {url}")
            return None
    except Exception as e:
        print(f"[naver] Error fetching {url}: {e}")
        return None

    soup = BeautifulSoup(resp.text, "html.parser")

    # Title
    title_el = (
        soup.select_one(".se-title-text")
        or soup.select_one("meta[property='og:title']")
        or soup.select_one(".tit_h3")
        or soup.select_one("h3.se_textarea")
        or soup.select_one("._postTitleText")
    )
    if title_el:
        title = title_el.get_text(strip=True) if title_el.name != "meta" else title_el.get("content", "")
    else:
        title = ""

    # Body
    body_el = (
        soup.select_one(".se-main-container")
        or soup.select_one("div.post-view")
        or soup.select_one("#postViewArea")
        or soup.select_one("div.__se_component_area")
        or soup.select_one(".sect_dsc")
    )
    content = body_el.get_text("\n", strip=True) if body_el else ""

    # Date
    date_el = (
        soup.select_one(".se_publishDate")
        or soup.select_one("meta[property='article:published_time']")
        or soup.select_one(".blog_date")
        or soup.select_one("p.date")
        or soup.select_one("span.date")
    )
    if date_el:
        pub_date = date_el.get_text(strip=True) if date_el.name != "meta" else date_el.get("content", "")
    else:
        pub_date = ""

    og_img = soup.select_one("meta[property='og:image']")
    thumbnail = og_img.get("content", "").strip() if og_img else ""

    images: list[str] = []
    body_root = body_el or soup
    for img in body_root.select("img[src], img[data-lazy-src], img[data-src]"):
        src = (
            img.get("data-lazy-src") or img.get("data-src") or img.get("src") or ""
        ).strip()
        if src and src not in images and not src.endswith(".gif"):
            if src.startswith("//"):
                src = "https:" + src
            images.append(src)

    if not content or len(content) < 30:
        print(f"[naver] Skipping (content too short): {url}")
        return None

    print(f"[naver] OK: '{title[:40]}' ({len(content)} chars, {len(images)} imgs)")
    return {
        "source": "naver",
        "title": title,
        "content": content,
        "url": url,
        "published_date": pub_date,
        "thumbnail": thumbnail,
        "images": images,
    }


async def scrape_naver() -> list[dict]:
    """Scrape all posts from the Naver blog."""
    # Try multiple methods to get URLs
    urls = await _get_post_urls_via_api()
    if not urls:
        urls = await _get_post_urls_via_rss()
    if not urls:
        urls = await _get_post_urls_via_playwright()

    if not urls:
        print("[naver] Could not find any post URLs")
        return []

    print(f"[naver] Total {len(urls)} posts to scrape")
    results: list[dict] = []

    async with httpx.AsyncClient(
        headers={
            "User-Agent": (
                "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) "
                "Version/16.0 Mobile/15E148 Safari/604.1"
            ),
        },
        follow_redirects=True,
        timeout=20,
    ) as client:
        for i, url in enumerate(urls, 1):
            post = await _scrape_post(client, url, i, len(urls))
            if post:
                results.append(post)
            await asyncio.sleep(1)

    print(f"[naver] Scraping complete: {len(results)} posts collected")
    return results
