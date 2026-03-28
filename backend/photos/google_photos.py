"""Google Photos Library API integration for searching and downloading photos."""

import os
from pathlib import Path

import httpx
from google import genai
from google.genai import types

from auth.google_auth import get_valid_access_token

PHOTOS_API = "https://photoslibrary.googleapis.com/v1"
_data_dir = Path(os.environ.get("DATA_DIR", str(Path(__file__).parent.parent / "data")))
DOWNLOAD_DIR = _data_dir / "photos"


async def search_photos(query: str, page_size: int = 20, page_token: str | None = None) -> dict:
    """Search Google Photos by text query (location, description, etc.)."""
    access_token = await get_valid_access_token()
    if not access_token:
        return {"error": "Google 계정이 연결되지 않았습니다. 먼저 로그인해주세요."}

    # The Photos Library API doesn't support free-text search directly via mediaItems:search,
    # but we can use the filters. For location-based search, we use the contentFilter
    # and also try listing with date/category filters.
    # However, the most flexible search is via mediaItems:search with filters.
    # For text-based search, we actually need to use the mediaItems endpoint differently.
    
    # Actually, Google Photos API v1 does NOT have a text search endpoint.
    # The mediaItems:search supports filters (date, content category, location) but not free text.
    # We'll use content category filters for travel/landscape and also try the description.
    
    # Best approach: list all media items and filter, OR use specific filters.
    # For practical use, we'll search by content categories and return results.
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    body: dict = {
        "pageSize": min(page_size, 100),
        "filters": {
            "contentFilter": {
                "includedContentCategories": ["TRAVEL", "LANDSCAPES", "CITYSCAPES"]
            },
        },
    }
    if page_token:
        body["pageToken"] = page_token

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            f"{PHOTOS_API}/mediaItems:search",
            headers=headers,
            json=body,
        )
        if resp.status_code != 200:
            return {"error": f"Google Photos API 오류: {resp.status_code} - {resp.text[:200]}"}

        data = resp.json()

    items = data.get("mediaItems", [])
    results = []
    query_lower = query.lower() if query else ""

    for item in items:
        desc = (item.get("description") or "").lower()
        filename = (item.get("filename") or "").lower()
        # Filter locally if a query is provided
        if query_lower and query_lower not in desc and query_lower not in filename:
            meta = item.get("mediaMetadata", {})
            loc = meta.get("location", {})
            loc_str = f"{loc.get('city', '')} {loc.get('country', '')}".lower()
            if query_lower not in loc_str:
                continue

        meta = item.get("mediaMetadata", {})
        results.append({
            "id": item["id"],
            "filename": item.get("filename", ""),
            "description": item.get("description", ""),
            "mimeType": item.get("mimeType", ""),
            "baseUrl": item.get("baseUrl", ""),
            "width": meta.get("width", ""),
            "height": meta.get("height", ""),
            "creationTime": meta.get("creationTime", ""),
            "thumbnailUrl": f"{item.get('baseUrl', '')}=w400-h300",
        })

    return {
        "photos": results,
        "nextPageToken": data.get("nextPageToken"),
        "total_results": len(results),
    }


async def get_photo_bytes(photo_id: str) -> tuple[bytes | None, str | None]:
    """Download original photo bytes by media item ID."""
    access_token = await get_valid_access_token()
    if not access_token:
        return None, "인증이 필요합니다."

    headers = {"Authorization": f"Bearer {access_token}"}

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(f"{PHOTOS_API}/mediaItems/{photo_id}", headers=headers)
        if resp.status_code != 200:
            return None, f"사진 정보 조회 실패: {resp.status_code}"

        item = resp.json()
        base_url = item.get("baseUrl", "")
        if not base_url:
            return None, "사진 URL을 가져올 수 없습니다."

        download_url = f"{base_url}=d"
        img_resp = await client.get(download_url)
        if img_resp.status_code != 200:
            return None, f"사진 다운로드 실패: {img_resp.status_code}"

        return img_resp.content, None


async def extract_locations_from_text(text: str) -> list[str]:
    """Use Gemini to extract location/place names from text."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return []

    client = genai.Client(api_key=api_key)
    prompt = f"""다음 블로그 글에서 사진을 검색하기에 적합한 장소명/지역명을 추출해주세요.
도시명, 관광지명, 건물명, 자연경관 이름 등을 포함합니다.
각 장소명을 한 줄에 하나씩, 다른 설명 없이 장소명만 출력해주세요.

글:
{text[:3000]}"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.1, max_output_tokens=512),
        )
        raw = response.text.strip()
        locations = [line.strip().strip("-").strip("•").strip() for line in raw.split("\n") if line.strip()]
        return [loc for loc in locations if len(loc) >= 2]
    except Exception as e:
        print(f"[photos] Location extraction failed: {e}", flush=True)
        return []
