import asyncio
import io
import os
import re
import zipfile
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from database import get_db
from models import Post
from scrapers.brunch_scraper import scrape_brunch
from scrapers.naver_scraper import scrape_naver

router = APIRouter()


async def _verify_cron_secret(
    authorization: str | None = Header(None),
    x_cron_secret: str | None = Header(None, alias="X-Cron-Secret"),
) -> None:
    """Bearer token or X-Cron-Secret must match CRON_SECRET (for scheduled / external cron)."""
    expected = os.getenv("CRON_SECRET", "").strip()
    if not expected:
        raise HTTPException(
            status_code=503,
            detail="CRON_SECRET is not set; scheduled scraping is disabled.",
        )
    token: str | None = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    elif x_cron_secret:
        token = x_cron_secret.strip()
    if not token or token != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing cron credentials.")


def _safe_filename(title: str, fallback: str, max_len: int = 100) -> str:
    base = (title or "").strip() or fallback
    base = re.sub(r'[<>:"/\\|?*\n\r\t]', "_", base)
    base = base[:max_len].strip(" .") or "post"
    return base


def _post_to_dict(p: Post) -> dict:
    return {
        "id": p.id,
        "source": p.source,
        "title": p.title,
        "content": p.content,
        "url": p.url,
        "published_date": p.published_date,
        "scraped_at": str(p.scraped_at) if p.scraped_at else None,
    }

scrape_status = {
    "is_running": False,
    "progress": "",
    "brunch_count": 0,
    "naver_count": 0,
    "error": None,
}


@router.get("/status")
async def get_scrape_status(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(func.count(Post.id)))
    total = result.scalar() or 0

    brunch_result = await db.execute(
        select(func.count(Post.id)).where(Post.source == "brunch")
    )
    brunch_count = brunch_result.scalar() or 0

    naver_result = await db.execute(
        select(func.count(Post.id)).where(Post.source == "naver")
    )
    naver_count = naver_result.scalar() or 0

    return {
        **scrape_status,
        "total_posts": total,
        "db_brunch_count": brunch_count,
        "db_naver_count": naver_count,
    }


def _begin_scrape_job() -> dict:
    """Shared kick-off for manual / scheduled runs."""
    if scrape_status["is_running"]:
        return {"message": "스크래핑이 이미 진행 중입니다.", "started": False}

    scrape_status["is_running"] = True
    scrape_status["error"] = None
    scrape_status["brunch_count"] = 0
    scrape_status["naver_count"] = 0
    scrape_status["progress"] = "브런치 블로그 스크래핑 시작..."

    asyncio.create_task(_run_scraping())
    return {"message": "스크래핑이 시작되었습니다.", "started": True}


@router.post("/start")
async def start_scraping():
    return _begin_scrape_job()


@router.post("/cron")
async def cron_scrape(_: None = Depends(_verify_cron_secret)):
    """스케줄러·GitHub Actions 등에서 호출해 브런치·네이버 글을 자동 아카이브합니다. CRON_SECRET 필요."""
    result = _begin_scrape_job()
    return {**result, "trigger": "cron"}


@router.post("/reset")
async def reset_scraping():
    """Force reset the scraping status if stuck."""
    scrape_status["is_running"] = False
    scrape_status["progress"] = "수동으로 초기화됨"
    scrape_status["error"] = None
    return {"message": "스크래핑 상태가 초기화되었습니다."}


async def _run_scraping():
    from database import async_session

    try:
        scrape_status["progress"] = "브런치 블로그 스크래핑 중..."
        brunch_posts = await scrape_brunch()
        scrape_status["brunch_count"] = len(brunch_posts)
        scrape_status["progress"] = f"브런치 {len(brunch_posts)}개 수집 완료. 네이버 블로그 스크래핑 중..."

        naver_posts = await scrape_naver()
        scrape_status["naver_count"] = len(naver_posts)
        scrape_status["progress"] = f"네이버 {len(naver_posts)}개 수집 완료. DB에 저장 중..."

        async with async_session() as db:
            all_posts = brunch_posts + naver_posts
            saved = 0
            for post_data in all_posts:
                existing = await db.execute(
                    select(Post).where(Post.url == post_data["url"])
                )
                if existing.scalar_one_or_none() is None:
                    db.add(Post(**post_data))
                    saved += 1
            await db.commit()

        scrape_status["progress"] = (
            f"완료! 브런치 {len(brunch_posts)}개, 네이버 {len(naver_posts)}개 수집. "
            f"신규 {saved}개 저장."
        )
    except Exception as e:
        scrape_status["error"] = str(e)
        scrape_status["progress"] = f"오류 발생: {str(e)}"
    finally:
        scrape_status["is_running"] = False


@router.get("/posts")
async def get_posts(
    source: str | None = None,
    page: int = 1,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    query = select(Post).order_by(Post.scraped_at.desc())
    if source:
        query = query.where(Post.source == source)

    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    posts = result.scalars().all()

    count_query = select(func.count(Post.id))
    if source:
        count_query = count_query.where(Post.source == source)
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    return {
        "posts": [
            {
                "id": p.id,
                "source": p.source,
                "title": p.title,
                "content": p.content[:300] + "..." if len(p.content) > 300 else p.content,
                "url": p.url,
                "published_date": p.published_date,
                "scraped_at": str(p.scraped_at) if p.scraped_at else None,
            }
            for p in posts
        ],
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.get("/posts/{post_id}")
async def get_post_detail(post_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        return {"error": "글을 찾을 수 없습니다."}
    return {
        "id": post.id,
        "source": post.source,
        "title": post.title,
        "content": post.content,
        "url": post.url,
        "published_date": post.published_date,
        "scraped_at": str(post.scraped_at) if post.scraped_at else None,
    }


@router.get("/export")
async def export_posts(
    export_format: Literal["json", "markdown"] = Query("json", alias="format"),
    source: Literal["brunch", "naver"] | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """DB에 저장된 글 전체를 JSON 또는 Markdown(zip)으로 내보냅니다. Google Sites 등 수동 이전·백업용."""
    query = select(Post).order_by(Post.id.asc())
    if source:
        query = query.where(Post.source == source)
    result = await db.execute(query)
    posts = result.scalars().all()

    if export_format == "json":
        payload = {
            "exported_at": datetime.utcnow().isoformat() + "Z",
            "count": len(posts),
            "posts": [_post_to_dict(p) for p in posts],
        }
        return JSONResponse(content=payload)

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        used_names: set[str] = set()
        for p in posts:
            base = _safe_filename(p.title, f"{p.source}_{p.id}")
            name = f"{base}.md"
            i = 2
            while name in used_names:
                name = f"{base}_{i}.md"
                i += 1
            used_names.add(name)
            header = (
                f"# {p.title}\n\n"
                f"- 출처: {p.source}\n"
                f"- 원본: {p.url}\n"
                f"- 게시일: {p.published_date or '(알 수 없음)'}\n\n"
                "---\n\n"
            )
            zf.writestr(name, header + p.content)
    buf.seek(0)
    stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    fname = f"istandby4u2_posts_{stamp}.zip"
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'},
    )
