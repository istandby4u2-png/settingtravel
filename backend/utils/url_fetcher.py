"""Fetch and extract readable text content from a URL."""

import re
import httpx
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright


MOBILE_UA = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
)
DESKTOP_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def _clean_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup.find_all(["script", "style", "nav", "footer", "header", "aside", "iframe", "noscript"]):
        tag.decompose()

    selectors = [
        "article",
        '[class*="post-content"]', '[class*="article-content"]', '[class*="entry-content"]',
        '[class*="post_ct"]', '[class*="se-main-container"]',
        '[class*="wrap_body"]', '[class*="content_body"]',
        ".tt_article_useless_p_margin",
        "main",
    ]
    content_el = None
    for sel in selectors:
        content_el = soup.select_one(sel)
        if content_el:
            break

    if not content_el:
        content_el = soup.find("body") or soup

    text = content_el.get_text(separator="\n", strip=True)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


async def _fetch_with_httpx(url: str) -> str | None:
    """Fast fetch using httpx (works for most static pages)."""
    try:
        async with httpx.AsyncClient(
            headers={"User-Agent": DESKTOP_UA},
            follow_redirects=True,
            timeout=15,
        ) as client:
            resp = await client.get(url)
            if resp.status_code == 200 and "text/html" in resp.headers.get("content-type", ""):
                return _clean_text(resp.text)
    except Exception:
        pass
    return None


async def _fetch_with_playwright(url: str) -> str | None:
    """Fallback: render JS-heavy pages with Playwright."""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(user_agent=DESKTOP_UA)
            await page.goto(url, wait_until="domcontentloaded", timeout=20000)
            await page.wait_for_timeout(2000)
            html = await page.content()
            await browser.close()
            return _clean_text(html)
    except Exception:
        pass
    return None


def _is_naver_blog(url: str) -> bool:
    return "blog.naver.com" in url


def _is_brunch(url: str) -> bool:
    return "brunch.co.kr" in url


async def _fetch_naver_blog(url: str) -> str | None:
    """Naver blogs load content inside an iframe; use mobile URL."""
    blog_match = re.search(r'blog\.naver\.com/(\w+)/(\d+)', url)
    if not blog_match:
        return None
    blog_id, log_no = blog_match.group(1), blog_match.group(2)
    mobile_url = f"https://m.blog.naver.com/{blog_id}/{log_no}"
    return await _fetch_with_httpx(mobile_url) or await _fetch_with_playwright(mobile_url)


async def fetch_url_content(url: str) -> dict:
    """
    Fetch readable text from a URL.
    Returns {"content": str, "url": str} on success,
            {"error": str} on failure.
    """
    url = url.strip()
    if not url.startswith("http"):
        url = "https://" + url

    try:
        text: str | None = None

        if _is_naver_blog(url):
            text = await _fetch_naver_blog(url)
        elif _is_brunch(url):
            text = await _fetch_with_playwright(url)
        else:
            text = await _fetch_with_httpx(url)
            if not text or len(text) < 100:
                text = await _fetch_with_playwright(url)

        if not text or len(text) < 50:
            return {"error": f"URL에서 충분한 텍스트를 추출할 수 없습니다: {url}"}

        return {"content": text, "url": url}
    except Exception as e:
        return {"error": f"URL 콘텐츠 가져오기 실패: {str(e)}"}
