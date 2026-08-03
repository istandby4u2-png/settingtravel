"""
Naver·Brunch 블로그에서 전체 글을 직접 수집해 Google Maps 링크를 추출합니다.
DB가 아닌 블로그 원본에서 읽으므로 누락 없이 모든 글을 커버합니다.
"""

import asyncio
import csv
import html as _html_mod
import io
import json
import os
import re
import time
import urllib.parse
from pathlib import Path

import httpx
from bs4 import BeautifulSoup
from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import Response

try:
    from google import genai as _genai
    from google.genai import types as _genai_types
    _GENAI_AVAILABLE = True
except ImportError:
    _GENAI_AVAILABLE = False

_DATA_DIR = Path(os.environ.get("DATA_DIR", "/tmp"))
_COLLECT_CSV = _DATA_DIR / "full_posts.csv"

# 백그라운드 수집 상태 (프로세스 내 공유)
_collect: dict = {"state": "idle", "done": 0, "total": 0, "started": 0.0, "error": ""}

SHEET_CSV_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1mZ5Mnmy7AgXJqQ3Gjufu-wbfpyW5UBCaWIV-b43GY-s"
    "/export?format=csv&gid=870337073"
)

CSV_HEADERS = [
    "Genre", "Title", "Writer / Director", "Publication date",
    "Travel Records by moonee", "Visit", "Reference", "Place", "Lat", "Lng",
]

router = APIRouter(tags=["maps"])

# ── 설정 ───────────────────────────────────────────────────────────────────────
NAVER_BLOG_ID = "istandby4u2"
BRUNCH_AUTHOR_ID = "istandby4u2"
BRUNCH_BASE = "https://brunch.co.kr"
BRUNCH_MAX_NO = 5000         # 스캔할 최대 글 번호 (삭제·비공개 갭 고려해 충분히 크게)
BRUNCH_CONSECUTIVE_STOP = 300 # 연속 404 이 수 이상이면 탐색 종료

_UA_DESKTOP = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
_UA_MOBILE = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
)

_GMAPS_RE = re.compile(
    r"https?://(?:"
    r"(?:www\.)?google\.com/maps[^\s\"'<>&)\]]*"
    r"|maps\.google\.(?:com|co\.\w+)[^\s\"'<>&)\]]*"
    r"|goo\.gl/maps/[^\s\"'<>&)\]]*"
    r"|maps\.app\.goo\.gl/[^\s\"'<>&)\]]*"
    r")",
    re.IGNORECASE,
)


# ── URL 유틸 ───────────────────────────────────────────────────────────────────

def _extract_coords(url: str) -> tuple[float, float] | None:
    # /maps/d/ URL은 My Maps 뷰어 — ll= 은 뷰포트 중심이라 핀 위치가 아님
    if "/maps/d/" in url:
        return None
    for pat in [
        r"@(-?\d+\.?\d*),(-?\d+\.?\d*)",
        r"[?&]ll=(-?\d+\.?\d*),(-?\d+\.?\d*)",
        r"[?&]q=(-?\d+\.?\d*)[,+](-?\d+\.?\d*)",
        r"[?&]center=(-?\d+\.?\d*),(-?\d+\.?\d*)",
        r"/(-?\d{1,3}\.\d{4,}),(-?\d{1,3}\.\d{4,})",
    ]:
        m = re.search(pat, url)
        if m:
            lat, lng = float(m.group(1)), float(m.group(2))
            if -90 <= lat <= 90 and -180 <= lng <= 180:
                return lat, lng
    return None


def _extract_place(url: str) -> str:
    m = re.search(r"/maps/place/([^/@?&]+)", url)
    if m:
        return urllib.parse.unquote_plus(m.group(1)).replace("+", " ")
    m = re.search(r"[?&]q=([^&]+)", url)
    if m:
        val = urllib.parse.unquote_plus(m.group(1))
        if not re.match(r"^-?\d+\.?\d*[,+]-?\d+\.?\d*$", val):
            return val
    return ""


async def _resolve_short_url(url: str, client: httpx.AsyncClient) -> str:
    if "goo.gl" not in url and "maps.app.goo.gl" not in url:
        return url
    try:
        r = await client.head(url, follow_redirects=True, timeout=8)
        return str(r.url)
    except Exception:
        return url


# ── HTML → Maps 링크 추출 ──────────────────────────────────────────────────────

async def _extract_maps_links(
    html: str, client: httpx.AsyncClient
) -> list[dict]:
    """HTML에서 Google Maps 링크 및 Naver 지도 컴포넌트를 추출해 좌표까지 파싱합니다."""
    soup = BeautifulSoup(html, "html.parser")
    seen_hrefs: set[str] = set()
    raw_items: list[dict] = []

    def _push(href: str, label: str = "") -> None:
        href = href.strip().rstrip(".,;)\"'")
        # My Maps 뷰어(/maps/d/)는 장소 핀이 아닌 지도 뷰포트 → 제외
        if "/maps/d/" in href:
            return
        if href and href not in seen_hrefs and _GMAPS_RE.match(href):
            seen_hrefs.add(href)
            raw_items.append({"href": href, "label": label})

    for a in soup.find_all("a", href=True):
        _push(a["href"], a.get_text(strip=True))
    for iframe in soup.find_all("iframe", src=True):
        _push(iframe["src"])
    for m in _GMAPS_RE.finditer(soup.get_text(" ")):
        _push(m.group(0))

    result = []
    seen_coords: set[tuple] = set()

    for item in raw_items:
        resolved = await _resolve_short_url(item["href"], client)
        coords = _extract_coords(resolved)
        place = _extract_place(resolved) or item["label"]
        if coords:
            k = (round(coords[0], 3), round(coords[1], 3))
            if k in seen_coords:
                continue
            seen_coords.add(k)
        result.append({"maps_url": resolved, "coords": coords, "place": place})

    # Naver Smart Editor 지도 컴포넌트에서 추가로 좌표 수집
    for entry in _extract_naver_map_data(soup):
        if entry["coords"]:
            k = (round(entry["coords"][0], 3), round(entry["coords"][1], 3))
            if k in seen_coords:
                continue
            seen_coords.add(k)
        result.append(entry)

    return result


def _extract_naver_map_data(soup: BeautifulSoup) -> list[dict]:
    """Naver Smart Editor의 data-linkdata map 컴포넌트에서 위치 정보를 추출합니다."""
    results: list[dict] = []
    seen: set[tuple] = set()

    for el in soup.find_all(attrs={"data-linkdata": True}):
        raw = el.get("data-linkdata", "")
        try:
            data = json.loads(_html_mod.unescape(raw))
        except Exception:
            continue
        lat_str = data.get("latitude")
        lng_str = data.get("longitude")
        if not lat_str or not lng_str:
            continue
        try:
            lat, lng = float(lat_str), float(lng_str)
        except Exception:
            continue
        if not (-90 <= lat <= 90 and -180 <= lng <= 180):
            continue
        k = (round(lat, 3), round(lng, 3))
        if k in seen:
            continue
        seen.add(k)

        name = data.get("name", "") or data.get("address", "")
        place_id = data.get("placeId", "")
        maps_url = (
            f"https://www.google.com/maps/place/?q=place_id:{place_id}"
            if place_id
            else f"https://www.google.com/maps/?q={lat},{lng}"
        )
        results.append({"maps_url": maps_url, "coords": (lat, lng), "place": name})

    return results


def _extract_work_title(essay_title: str) -> str:
    """Essay Title의 <>, 《》, ⟪⟫, 『』, ' '(곱슬), ' '(ASCII), [] 안에서 작품명을 추출합니다."""
    for pat in [
        r"<([^<>]+)>",            # <작품명>
        r"《([^《》]+)》",          # 《작품명》  U+300A/300B
        r"⟪([^⟪⟫]+)⟫",          # ⟪작품명⟫  U+27EA/27EB
        r"『([^『』]+)』",          # 『작품명』  U+300E/300F
        r"‘([^‘’]{2,})’",  # '작품명' 곱슬 따옴표
        r"'([^']{2,})'",          # '작품명' ASCII 따옴표 (2자 이상)
        r"\[([^\[\]]+)\]",        # [시리즈명]
    ]:
        m = re.search(pat, essay_title)
        if m:
            return m.group(1).strip()
    return ""


def _classify_batch_sync(api_key: str, batch: list[tuple[str, str]]) -> dict[str, str]:
    """단일 배치를 Gemini로 분류합니다 (동기, to_thread에서 실행)."""
    lines = "\n".join(
        f'{i+1}. "{wt}" (참고: {et[:50]})'
        for i, (wt, et) in enumerate(batch)
    )
    prompt = (
        "아래 작품들이 Book(소설/시/에세이), Movie(영화), Drama(드라마/TV)인지 분류하세요.\n"
        "셋 중 해당 없으면 빈 문자열입니다.\n\n"
        f"{lines}\n\n"
        "JSON만 출력: {\"1\":\"Book\",\"2\":\"Movie\",\"3\":\"Drama\",\"4\":\"\", ...}"
    )
    client = _genai.Client(api_key=api_key)
    resp = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[_genai_types.Content(role="user", parts=[_genai_types.Part(text=prompt)])],
        config=_genai_types.GenerateContentConfig(temperature=0.1, max_output_tokens=2048),
    )
    raw = resp.text.strip()
    clean = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
    clean = re.sub(r"\s*```\s*$", "", clean.strip())
    m = re.search(r"\{.*\}", clean, re.DOTALL)
    if not m:
        print(f"[genre_classify] 배치 파싱 실패: {raw[:150]}", flush=True)
        return {}
    classified = json.loads(m.group(0))
    result: dict[str, str] = {}
    for i, (wt, _) in enumerate(batch):
        val = classified.get(str(i + 1), "")
        result[wt] = val if val in ("Book", "Movie", "Drama") else ""
    return result


async def _classify_genres_ai(works: list[tuple[str, str]]) -> dict[str, str]:
    """
    Gemini API로 작품명 목록의 Genre를 분류합니다 (배치 20개씩 처리).
    works: [(work_title, essay_title_sample), ...]
    반환: {work_title: "Book" | "Movie" | "Drama" | ""}
    """
    api_key = os.getenv("GOOGLE_API_KEY", "")
    if not _GENAI_AVAILABLE or not api_key or api_key == "your_gemini_api_key_here":
        return {}

    # 중복 제거
    unique: dict[str, str] = {}
    for wt, et in works:
        if wt and wt not in unique:
            unique[wt] = et

    if not unique:
        return {}

    items = list(unique.items())
    batch_size = 20
    result: dict[str, str] = {}

    print(f"[genre_classify] 분류 시작: {len(items)}개 작품, {(len(items)-1)//batch_size+1}개 배치", flush=True)

    for start in range(0, len(items), batch_size):
        batch = items[start: start + batch_size]
        try:
            batch_result = await asyncio.to_thread(_classify_batch_sync, api_key, batch)
            result.update(batch_result)
            classified_cnt = sum(1 for v in batch_result.values() if v)
            print(f"[genre_classify] 배치 {start//batch_size+1}: {classified_cnt}/{len(batch)}개 분류됨", flush=True)
        except Exception as e:
            print(f"[genre_classify] 배치 오류: {e}", flush=True)
        await asyncio.sleep(1)  # API 레이트 리밋 방지

    print(f"[genre_classify] 전체 완료: {sum(1 for v in result.values() if v)}개 분류됨", flush=True)
    return result


def _parse_title(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    og = soup.select_one("meta[property='og:title']")
    return og.get("content", "").strip() if og else ""


# ── Naver 전체 글 수집 ─────────────────────────────────────────────────────────

_NAVER_HEADERS = {
    "User-Agent": _UA_MOBILE,
    "Referer": f"https://m.blog.naver.com/{NAVER_BLOG_ID}",
}


async def _naver_category_nos() -> list[int]:
    """블로그 카테고리 번호 목록을 가져옵니다. 실패 시 [0] 반환."""
    try:
        async with httpx.AsyncClient(headers=_NAVER_HEADERS, follow_redirects=True, timeout=10) as client:
            r = await client.get(
                f"https://m.blog.naver.com/api/blogs/{NAVER_BLOG_ID}/categories"
            )
            if r.status_code == 200:
                cats = r.json().get("result", {}).get("categories", [])
                nos = {0}  # 0 = 전체
                for c in cats:
                    if no := c.get("categoryNo"):
                        nos.add(int(no))
                return list(nos)
    except Exception:
        pass
    return [0]


async def _naver_urls_by_category(cat_no: int) -> list[str]:
    """특정 카테고리의 전체 포스트 URL을 수집합니다."""
    urls: list[str] = []
    page = 1
    item_count = 30
    async with httpx.AsyncClient(headers=_NAVER_HEADERS, follow_redirects=True, timeout=15) as client:
        while True:
            api = (
                f"https://m.blog.naver.com/api/blogs/{NAVER_BLOG_ID}/post-list"
                f"?categoryNo={cat_no}&itemCount={item_count}&page={page}"
            )
            try:
                r = await client.get(api)
                if r.status_code != 200:
                    break
                data = r.json()
            except Exception:
                break
            items = data.get("result", {}).get("items", [])
            if not items:
                break
            for item in items:
                if log_no := item.get("logNo"):
                    urls.append(f"https://m.blog.naver.com/{NAVER_BLOG_ID}/{log_no}")
            # 응답에 hasNext 필드가 없으므로 받은 아이템 수로 종료 판단
            if len(items) < item_count:
                break
            page += 1
            await asyncio.sleep(0.3)
    return urls


async def _naver_all_urls() -> list[str]:
    """모든 카테고리에서 Naver 블로그 전체 포스트 URL을 수집합니다."""
    cat_nos = await _naver_category_nos()
    # 카테고리별로 병렬 수집
    results = await asyncio.gather(*[_naver_urls_by_category(no) for no in cat_nos])
    # 중복 제거 (같은 글이 여러 카테고리에 노출될 수 있음)
    seen: set[str] = set()
    urls: list[str] = []
    for group in results:
        for url in group:
            if url not in seen:
                seen.add(url)
                urls.append(url)
    return urls


async def _scan_naver(sem: asyncio.Semaphore) -> list[dict]:
    """Naver 전체 글에서 Google Maps 링크를 추출합니다."""
    urls = await _naver_all_urls()
    entries: list[dict] = []

    async with httpx.AsyncClient(
        headers={"User-Agent": _UA_MOBILE},
        follow_redirects=True,
        timeout=15,
    ) as client:
        async def process(url: str) -> list[dict]:
            async with sem:
                await asyncio.sleep(0.5)
                try:
                    r = await client.get(url)
                    if r.status_code != 200:
                        return []
                    title = _parse_title(r.text)
                    links = await _extract_maps_links(r.text, client)
                    return [
                        {
                            "source": "naver",
                            "post_url": url,
                            "post_title": title,
                            "place": lk["place"],
                            "maps_url": lk["maps_url"],
                            "coords": (
                                {"lat": lk["coords"][0], "lng": lk["coords"][1]}
                                if lk["coords"] else None
                            ),
                        }
                        for lk in links
                    ]
                except Exception:
                    return []

        results = await asyncio.gather(*(process(u) for u in urls))
        for group in results:
            entries.extend(group)

    return entries


# ── Brunch 전체 글 수집 ────────────────────────────────────────────────────────

_BRUNCH_ART_RE = re.compile(rf"/@{BRUNCH_AUTHOR_ID}/(\d+)(?:[\"'\s?#]|$)")


async def _brunch_urls_from_author_page(client: httpx.AsyncClient) -> set[int]:
    """작가 페이지 HTML에서 글 번호를 직접 파싱합니다 (빠른 첫 시도)."""
    nos: set[int] = set()
    try:
        r = await client.get(
            f"{BRUNCH_BASE}/@{BRUNCH_AUTHOR_ID}",
            headers={"User-Agent": _UA_DESKTOP},
            timeout=15,
        )
        for m in _BRUNCH_ART_RE.finditer(r.text):
            nos.add(int(m.group(1)))
    except Exception:
        pass
    return nos


async def _brunch_all_urls() -> list[str]:
    """
    브런치 전체 글 URL 수집 — 두 가지 방법 병행:
    1. 작가 페이지 HTML 파싱 (빠름, 일부만 나올 수 있음)
    2. 순차 HEAD 탐색 (느리지만 확실 — 충분한 연속 404 허용)
    두 결과를 합쳐 중복 제거 후 반환합니다.
    """
    async with httpx.AsyncClient(follow_redirects=True, timeout=10) as client:
        # ① 작가 페이지에서 빠르게 번호 수집
        page_nos = await _brunch_urls_from_author_page(client)

        # ② 순차 HEAD 탐색 (삭제·비공개로 생긴 큰 갭 통과)
        found_nos: set[int] = set(page_nos)
        consecutive = 0

        for no in range(1, BRUNCH_MAX_NO + 1):
            url = f"{BRUNCH_BASE}/@{BRUNCH_AUTHOR_ID}/{no}"
            try:
                r = await client.head(url, headers={"User-Agent": _UA_DESKTOP})
                if r.status_code == 200:
                    found_nos.add(no)
                    consecutive = 0
                else:
                    consecutive += 1
            except Exception:
                consecutive += 1
            if consecutive >= BRUNCH_CONSECUTIVE_STOP:
                break
            await asyncio.sleep(0.1)

    return [f"{BRUNCH_BASE}/@{BRUNCH_AUTHOR_ID}/{no}" for no in sorted(found_nos)]


async def _scan_brunch(sem: asyncio.Semaphore) -> list[dict]:
    """브런치 전체 글에서 Google Maps 링크를 추출합니다."""
    urls = await _brunch_all_urls()
    entries: list[dict] = []

    async with httpx.AsyncClient(
        headers={"User-Agent": _UA_DESKTOP},
        follow_redirects=True,
        timeout=15,
    ) as client:
        async def process(url: str) -> list[dict]:
            async with sem:
                await asyncio.sleep(0.4)
                try:
                    r = await client.get(url)
                    if r.status_code != 200:
                        return []
                    title = _parse_title(r.text)
                    links = await _extract_maps_links(r.text, client)
                    return [
                        {
                            "source": "brunch",
                            "post_url": url,
                            "post_title": title,
                            "place": lk["place"],
                            "maps_url": lk["maps_url"],
                            "coords": (
                                {"lat": lk["coords"][0], "lng": lk["coords"][1]}
                                if lk["coords"] else None
                            ),
                        }
                        for lk in links
                    ]
                except Exception:
                    return []

        results = await asyncio.gather(*(process(u) for u in urls))
        for group in results:
            entries.extend(group)

    return entries


# ── 전체 스캔 ──────────────────────────────────────────────────────────────────

async def _scan_all() -> list[dict]:
    """Naver + Brunch 양쪽에서 Google Maps 링크를 동시에 수집합니다."""
    sem = asyncio.Semaphore(5)
    naver_entries, brunch_entries = await asyncio.gather(
        _scan_naver(sem),
        _scan_brunch(sem),
    )
    return naver_entries + brunch_entries


# ── KML 생성 ───────────────────────────────────────────────────────────────────

def _make_kml(entries: list[dict]) -> str:
    def esc(s: str) -> str:
        return (
            s.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )

    marks: list[str] = []
    for e in entries:
        if not e.get("coords"):
            continue
        lat = e["coords"]["lat"]
        lng = e["coords"]["lng"]
        name = esc(e.get("place") or e.get("post_title") or "")
        post_title = esc(e.get("post_title", ""))
        post_url = e.get("post_url", "")
        source = e.get("source", "")
        marks.append(
            f"    <Placemark>\n"
            f"      <name>{name}</name>\n"
            f"      <description>"
            f'<![CDATA[<b>[{source}]</b> <a href="{post_url}">{post_title}</a>]]>'
            f"</description>\n"
            f"      <Point><coordinates>{lng},{lat},0</coordinates></Point>\n"
            f"    </Placemark>"
        )

    body = "\n".join(marks)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<kml xmlns="http://www.opengis.net/kml/2.2">\n'
        "  <Document>\n"
        "    <name>배경여행 여행지</name>\n"
        f"{body}\n"
        "  </Document>\n"
        "</kml>"
    )


# ── 엔드포인트 ─────────────────────────────────────────────────────────────────

async def _fetch_sheet() -> list[dict]:
    """Google Sheets CSV를 가져옵니다."""
    async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
        r = await client.get(SHEET_CSV_URL)
        r.raise_for_status()
        reader = csv.DictReader(io.StringIO(r.text))
        return list(reader)


def _norm(url: str) -> str:
    return url.strip().rstrip("/")


def _make_csv(sheet_rows: list[dict], scan_entries: list[dict]) -> str:
    """스프레드시트 행과 스캔 결과를 매칭해 동일 형식의 CSV를 생성합니다."""

    # 스캔 결과를 정규화된 URL로 인덱싱
    maps_by_url: dict[str, list[dict]] = {}
    for entry in scan_entries:
        key = _norm(entry["post_url"])
        maps_by_url.setdefault(key, []).append(entry)

    output_rows: list[dict] = []
    matched_keys: set[str] = set()

    for row in sheet_rows:
        travel = row.get("Travel Records by moonee", "").strip()
        key = _norm(travel)

        # 블로그 URL이 있고 스캔 결과와 매칭되는 경우
        if key and key in maps_by_url:
            matched_keys.add(key)
            for entry in maps_by_url[key]:
                coords = entry.get("coords") or {}
                output_rows.append({
                    "Genre": row.get("Genre", ""),
                    "Title": row.get("Title", ""),
                    "Writer / Director": row.get("Writer / Director", ""),
                    "Publication date": row.get("Publication date", ""),
                    "Travel Records by moonee": travel,
                    "Visit": row.get("Visit", ""),
                    "Reference": entry.get("maps_url", ""),
                    "Place": entry.get("place", ""),
                    "Lat": coords.get("lat", ""),
                    "Lng": coords.get("lng", ""),
                })

    # 스프레드시트에 없는 포스트 (매칭 안 된 스캔 결과)
    for entry in scan_entries:
        if _norm(entry["post_url"]) not in matched_keys:
            coords = entry.get("coords") or {}
            output_rows.append({
                "Genre": "",
                "Title": entry.get("post_title", ""),
                "Writer / Director": "",
                "Publication date": "",
                "Travel Records by moonee": entry.get("post_url", ""),
                "Visit": "",
                "Reference": entry.get("maps_url", ""),
                "Place": entry.get("place", ""),
                "Lat": coords.get("lat", ""),
                "Lng": coords.get("lng", ""),
            })

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=CSV_HEADERS, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(output_rows)
    return buf.getvalue()


@router.get("/api/maps/scan")
async def scan():
    """Naver·Brunch 전체 글에서 Google Maps 링크를 스캔합니다 (1~3분 소요)."""
    entries = await _scan_all()
    with_coords = [e for e in entries if e.get("coords")]
    return {
        "total_links": len(entries),
        "with_coords": len(with_coords),
        "results": entries,
    }


@router.get("/api/maps/kml")
async def download_kml():
    """Google Maps 링크를 KML로 내보냅니다. My Maps 가져오기(import)에 사용하세요."""
    entries = await _scan_all()
    kml = _make_kml(entries)
    return Response(
        content=kml.encode("utf-8"),
        media_type="application/vnd.google-earth.kml+xml",
        headers={"Content-Disposition": 'attachment; filename="baegyeong-travel.kml"'},
    )


@router.get("/api/maps/csv")
async def download_csv():
    """스프레드시트와 동일 형식(7컬럼+Lat/Lng)의 CSV를 반환합니다.
    스프레드시트 'Travel Records by moonee'의 블로그 URL과 매칭해 Genre/Title/Writer를 채웁니다."""
    sheet_rows, scan_entries = await asyncio.gather(
        _fetch_sheet(),
        _scan_all(),
    )
    csv_text = _make_csv(sheet_rows, scan_entries)
    return Response(
        content=("﻿" + csv_text).encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="baegyeong-maps.csv"'},
    )


# ── My Maps import 준비 ────────────────────────────────────────────────────────

SECOND_SHEET_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1NpCN7gKrtrARc1f_9QV2DUGfw9qqjCvTBEB9K7Gs018"
    "/export?format=csv&gid=0"
)

BUILD_HEADERS = [
    "Genre", "Work Title", "Essay Title", "Essay By moonee", "Visit",
    "Latitude", "Longitude",
]


async def _fetch_second_sheet() -> list[dict]:
    async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
        r = await client.get(SECOND_SHEET_URL)
        r.raise_for_status()
        rows = list(csv.DictReader(io.StringIO(r.text)))
        # 빈 행 제거
        return [r for r in rows if any(v.strip() for v in r.values())]


def _row_key(url: str, lat: float, lng: float) -> tuple:
    """중복 감지용 키: URL + 소수점 3자리 좌표."""
    return (_norm(url), round(lat, 3), round(lng, 3))


def _squash(s: str) -> str:
    return re.sub(r"\s+", "", s or "").lower()


def _build_work_index(sheet_rows: list[dict]) -> list[tuple[str, str, str]]:
    """작품명으로 글을 찾기 위한 색인. (정규화 제목, 원래 제목, 장르) 목록.

    첫 번째 시트에 블로그 URL이 붙어 있는 행은 절반이 안 된다. 나머지는 글 제목에
    작품명이 들어 있는 경우가 많아('<고독한 미식가>에 등장하는 미유키식당') 제목으로도 찾는다.
    긴 제목부터 맞춰 봐야 짧은 제목이 먼저 걸리는 오탐을 피할 수 있다.
    """
    index: dict[str, tuple[str, str]] = {}
    for row in sheet_rows:
        title = (row.get("Title") or "").strip()
        if len(title) < 2:
            continue
        index.setdefault(_squash(title), (title, (row.get("Genre") or "").strip()))
    return sorted(
        ((k, t, g) for k, (t, g) in index.items()), key=lambda x: -len(x[0])
    )


def _match_work(essay_title: str, work_index: list[tuple[str, str, str]]) -> tuple[str, str]:
    """글 제목에 들어 있는 작품명을 찾아 (작품명, 장르) 를 돌려준다."""
    squashed = _squash(essay_title)
    for key, title, genre in work_index:
        if key in squashed:
            return title, genre
    return "", ""


@router.get("/api/maps/build-sheet")
async def build_sheet():
    """
    두 스프레드시트 + 블로그 전체 스캔을 합쳐 완성된 CSV를 반환합니다.

    파이프라인:
      1. 첫 번째 시트 (1mZ5...) → 블로그 URL ▶ Genre / Work Title / Visit 매핑
      2. 두 번째 시트 (1NpC...) → 기존 12행 보존 + Visit 보강
      3. 블로그 전체 스캔  → Maps 링크가 있는 새 포스트 추가
      4. 중복 제거 후 정렬, 7컬럼 CSV 반환
    """
    # ── 세 소스 병렬 수집 ────────────────────────────────────────────────────────
    first_sheet, second_sheet, scan_entries = await asyncio.gather(
        _fetch_sheet(),        # 첫 번째 시트: Genre/Title/Visit
        _fetch_second_sheet(), # 두 번째 시트: 기존 큐레이션 데이터
        _scan_all(),           # 블로그 스캔: Maps 링크
    )

    # ── 첫 번째 시트로 URL → 메타데이터 매핑 ────────────────────────────────────
    meta_by_url: dict[str, dict] = {}
    for row in first_sheet:
        travel = row.get("Travel Records by moonee", "").strip()
        if not travel:
            continue
        key = _norm(travel)
        if key not in meta_by_url:
            meta_by_url[key] = {
                "Genre": row.get("Genre", ""),
                "Work Title": row.get("Title", ""),
                "Visit": row.get("Visit", ""),
            }

    work_index = _build_work_index(first_sheet)

    # 같은 글이 브런치·네이버 양쪽에 있으면 브런치 링크를 쓴다.
    # 네이버에는 브런치 글을 다시 올린 것이 섞여 있다.
    brunch_url_by_title: dict[str, str] = {}
    title_by_url: dict[str, str] = {}
    for entry in scan_entries:
        post_url = entry.get("post_url", "")
        title_key = _squash(entry.get("post_title", ""))
        if not title_key:
            continue
        title_by_url.setdefault(_norm(post_url), title_key)
        if "brunch.co.kr" in post_url:
            brunch_url_by_title.setdefault(title_key, post_url)

    def prefer_brunch(post_url: str, essay_title: str = "") -> str:
        if "brunch.co.kr" in post_url:
            return post_url
        key = _squash(essay_title) or title_by_url.get(_norm(post_url), "")
        return brunch_url_by_title.get(key, post_url)

    # ── 두 번째 시트 기존 행 보존 ────────────────────────────────────────────────
    seen: set[tuple] = set()
    output: list[dict] = []

    for row in second_sheet:
        url = prefer_brunch(row.get("Essay By moonee", "").strip(), row.get("Essay Title", ""))
        lat_str = row.get("Latitude", "").strip()
        lng_str = row.get("Longitude", "").strip()
        if not lat_str or not lng_str:
            continue
        try:
            lat, lng = float(lat_str), float(lng_str)
        except ValueError:
            continue

        k = _row_key(url, lat, lng)
        if k in seen:
            continue
        seen.add(k)

        # Visit가 비어 있으면 첫 번째 시트에서 보강
        visit = row.get("Visit", "").strip().lstrip("(").rstrip(")")
        if not visit or visit == "없음":
            visit = meta_by_url.get(_norm(url), {}).get("Visit", "")

        output.append({
            "Genre":            row.get("Genre", ""),
            "Work Title":       row.get("Work Title", ""),
            "Essay Title":      row.get("Essay Title", ""),
            "Essay By moonee":  url,
            "Visit":            visit,
            "Latitude":         lat,
            "Longitude":        lng,
        })

    # ── 블로그 스캔 결과 중 신규 항목 추가 ───────────────────────────────────────
    for entry in scan_entries:
        if not entry.get("coords"):
            continue

        url = prefer_brunch(entry.get("post_url", ""), entry.get("post_title", ""))
        lat = entry["coords"]["lat"]
        lng = entry["coords"]["lng"]
        k = _row_key(url, lat, lng)
        if k in seen:
            continue
        seen.add(k)

        meta = meta_by_url.get(_norm(entry.get("post_url", "")), {}) or meta_by_url.get(_norm(url), {})
        essay_title = entry.get("post_title", "")
        genre, work_title = meta.get("Genre", ""), meta.get("Work Title", "")
        if not work_title:  # URL 매칭이 안 되면 글 제목에서 작품명을 찾는다
            work_title, matched_genre = _match_work(essay_title, work_index)
            genre = genre or matched_genre

        output.append({
            "Genre":            genre,
            "Work Title":       work_title,
            "Essay Title":      essay_title,
            "Essay By moonee":  url,
            "Visit":            meta.get("Visit", ""),
            "Latitude":         lat,
            "Longitude":        lng,
        })

    # ── 마커 이름이 비지 않도록 Work Title 을 Essay Title 로 채운다 ──────────────
    # My Maps 는 Work Title 을 마커 이름으로 쓰는데, 글 제목에 작품명이 없는 글
    # (연재물·장소 중심 에세이)이 많아 그대로 두면 핀이 '제목 없음' 으로 뜬다.
    for row in output:
        if not row["Work Title"].strip():
            row["Work Title"] = row["Essay Title"]

    # ── 정렬: Genre 있는 행 먼저, 이후 Genre → Work Title → Essay Title 순 ──────
    output.sort(key=lambda r: (
        0 if r["Genre"] else 1,
        r.get("Genre", ""),
        r.get("Work Title", ""),
        r.get("Essay Title", ""),
    ))

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=BUILD_HEADERS, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(output)

    return Response(
        content=("﻿" + buf.getvalue()).encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="mymaps-complete.csv"'},
    )


# ── 전체 글 백그라운드 수집 ────────────────────────────────────────────────────

async def _run_full_collect() -> None:
    """
    Naver(~200) + Brunch(~150) 전체 글을 수집합니다.
    Maps 링크가 있으면 Lat/Lng 포함, 없는 글도 목록에 올립니다.
    결과는 _COLLECT_CSV 파일에 저장합니다.
    """
    global _collect
    _collect = {"state": "running", "done": 0, "total": 0, "started": time.time(), "error": ""}

    try:
        # ── 첫 번째 시트: URL → Genre / Work Title / Visit ──────────────────────
        first_sheet = await _fetch_sheet()
        meta_by_url: dict[str, dict] = {}
        for row in first_sheet:
            travel = row.get("Travel Records by moonee", "").strip()
            if not travel:
                continue
            k = _norm(travel)
            if k not in meta_by_url:
                meta_by_url[k] = {
                    "Genre":      row.get("Genre", ""),
                    "Work Title": row.get("Title", ""),
                    "Visit":      row.get("Visit", ""),
                }

        # ── 전체 포스트 URL 수집 (병렬) ─────────────────────────────────────────
        naver_urls, brunch_urls = await asyncio.gather(
            _naver_all_urls(),
            _brunch_all_urls(),
        )
        all_posts = (
            [(u, "naver",  _UA_MOBILE)   for u in naver_urls] +
            [(u, "brunch", _UA_DESKTOP)  for u in brunch_urls]
        )
        _collect["total"] = len(all_posts)

        # ── 각 포스트 HTML 수집 + Maps 링크 추출 ────────────────────────────────
        sem = asyncio.Semaphore(4)
        rows: list[dict] = []

        async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:

            async def _process(url: str, source: str, ua: str) -> list[dict]:
                async with sem:
                    await asyncio.sleep(0.5 if source == "naver" else 0.4)
                    try:
                        r = await client.get(url, headers={"User-Agent": ua})
                        if r.status_code != 200:
                            return []
                        html = r.text
                        title = _parse_title(html)
                        links = await _extract_maps_links(html, client)
                    except Exception:
                        return []
                    finally:
                        _collect["done"] += 1

                    meta = meta_by_url.get(_norm(url), {})
                    work_title = meta.get("Work Title", "") or _extract_work_title(title)
                    base = {
                        "Genre":           meta.get("Genre", ""),
                        "Work Title":      work_title,
                        "Essay Title":     title,
                        "Essay By moonee": url,
                        "Visit":           meta.get("Visit", ""),
                    }

                    if not links:
                        return [{**base, "Latitude": "", "Longitude": ""}]

                    # 좌표 있는 항목 우선; 없으면 전체 포함
                    with_coords = [lk for lk in links if lk.get("coords")]
                    use = with_coords if with_coords else links

                    result = []
                    for lk in use:
                        coords = lk.get("coords")
                        result.append({
                            **base,
                            "Latitude":  coords[0] if coords else "",
                            "Longitude": coords[1] if coords else "",
                        })
                    return result

            groups = await asyncio.gather(*[_process(u, s, ua) for u, s, ua in all_posts])
            for g in groups:
                rows.extend(g)

        # ── AI Genre 분류 (Genre가 비어 있고 Work Title이 있는 행) ──────────────
        unclassified = [
            (r["Work Title"], r["Essay Title"])
            for r in rows
            if r.get("Work Title") and not r.get("Genre")
        ]
        if unclassified:
            genre_map = await _classify_genres_ai(unclassified)
            if genre_map:
                for r in rows:
                    if not r.get("Genre") and r.get("Work Title"):
                        r["Genre"] = genre_map.get(r["Work Title"], "")

        # ── 정렬 ────────────────────────────────────────────────────────────────
        rows.sort(key=lambda r: (
            0 if r["Genre"] else 1,
            r.get("Genre", ""),
            r.get("Work Title", ""),
            r.get("Essay Title", ""),
        ))

        # ── CSV 저장 ─────────────────────────────────────────────────────────────
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=BUILD_HEADERS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
        _COLLECT_CSV.write_text("﻿" + buf.getvalue(), encoding="utf-8")

        _collect["state"] = "done"

    except Exception as exc:
        _collect["state"] = "error"
        _collect["error"] = str(exc)


@router.post("/api/maps/collect")
async def start_collect(background_tasks: BackgroundTasks):
    """전체 글 수집을 백그라운드로 시작합니다. 이미 실행 중이면 무시합니다."""
    if _collect["state"] == "running":
        return {"state": "already_running", **_collect}
    background_tasks.add_task(_run_full_collect)
    return {"state": "started", "message": "수집을 시작했습니다. /api/maps/collect 로 진행 상황을 확인하세요."}


@router.get("/api/maps/collect")
async def collect_status():
    """수집 진행 상황을 반환합니다."""
    elapsed = round(time.time() - _collect["started"], 1) if _collect["started"] else 0
    return {
        **_collect,
        "elapsed_sec": elapsed,
        "csv_ready": _COLLECT_CSV.exists() and _collect["state"] == "done",
    }


@router.get("/api/maps/classify-test")
async def classify_test():
    """Gemini Genre 분류 동작 확인용 (소량 샘플 테스트)."""
    samples = [
        ("노르웨이의 숲", "<노르웨이의 숲> 배경여행"),
        ("고독한 미식가", "<고독한 미식가>에 등장한 맛집"),
        ("8월의 크리스마스", "군산여행 ㅡ '8월의 크리스마스' 속 그곳"),
        ("N을 위하여", "<N을 위하여>가 시작되는 섬"),
        ("MAGIC", "SEKAI NO OWARI, 'MAGIC'에 등장하는 카페"),
    ]
    result = await _classify_genres_ai(samples)
    return {"classified": result, "genai_available": _GENAI_AVAILABLE,
            "api_key_set": bool(os.getenv("GOOGLE_API_KEY"))}


@router.get("/api/maps/collect/csv")
async def collect_csv():
    """수집 완료된 CSV를 다운로드합니다."""
    if not _COLLECT_CSV.exists():
        return Response(content="아직 수집이 완료되지 않았습니다. POST /api/maps/collect 로 먼저 시작하세요.",
                        status_code=404, media_type="text/plain; charset=utf-8")
    return Response(
        content=_COLLECT_CSV.read_bytes(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="all-posts.csv"'},
    )
