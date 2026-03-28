"""공개 블로그용 읽기 전용 API (수집 글 노출)."""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Post

router = APIRouter()


@router.get("/posts")
async def list_public_posts(
    source: Literal["brunch", "naver"] | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(12, ge=1, le=50),
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
    total = (await db.execute(count_query)).scalar() or 0

    return {
        "posts": [
            {
                "id": p.id,
                "source": p.source,
                "title": p.title,
                "excerpt": (p.content[:280] + "…") if len(p.content) > 280 else p.content,
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
async def get_public_post(post_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="글을 찾을 수 없습니다.")

    return {
        "id": post.id,
        "source": post.source,
        "title": post.title,
        "content": post.content,
        "url": post.url,
        "published_date": post.published_date,
        "scraped_at": str(post.scraped_at) if post.scraped_at else None,
    }
