"""공개 블로그용 읽기 전용 API (수집 글 노출)."""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import Integer, and_, func, or_, select, tuple_
from sqlalchemy.orm import aliased
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Post

router = APIRouter()


def _norm_title(col):
    """공백을 지우고 소문자로. 같은 글이 두 곳에 올라갈 때 띄어쓰기가 달라지는 경우가 있다."""
    return func.replace(func.lower(col), " ", "")


def _naver_date_key(col):
    """네이버 발행일('2018. 4. 14. 13:49')을 정렬 가능한 정수 20180414 로."""
    rest = func.substr(col, 7)  # 'M. D. HH:MM'
    month_len = func.instr(rest, ".") - 1
    rest2 = func.substr(rest, month_len + 3)  # 'D. HH:MM'
    day_len = func.instr(rest2, ".") - 1
    return (
        func.cast(func.substr(col, 1, 4), Integer) * 10000
        + func.cast(func.substr(rest, 1, month_len), Integer) * 100
        + func.cast(func.substr(rest2, 1, day_len), Integer)
    )


def _dedupe_by_title():
    """제목이 겹치는 글을 하나만 남기는 조건.

    - 브런치와 네이버 양쪽에 있으면 브런치를 남긴다. 네이버에는 브런치 글을 다시 올린 것이
      섞여 있다.
    - 네이버끼리 겹치면 먼저 발행된 원본을 남긴다.

    스크래핑이 매일 다시 돌기 때문에 DB에서 지우면 다음 날 되살아난다. 그래서 조회 시점에
    걸러 낸다.
    """
    brunch_titles = (
        select(_norm_title(Post.title)).where(Post.source == "brunch").scalar_subquery()
    )
    not_reposted_to_naver = or_(
        Post.source != "naver", _norm_title(Post.title).notin_(brunch_titles)
    )

    earlier = aliased(Post)
    has_earlier_naver_twin = (
        select(earlier.id)
        .where(
            earlier.source == "naver",
            Post.source == "naver",
            _norm_title(earlier.title) == _norm_title(Post.title),
            earlier.id != Post.id,
            tuple_(_naver_date_key(earlier.published_date), earlier.id)
            < tuple_(_naver_date_key(Post.published_date), Post.id),
        )
        .exists()
    )

    return and_(not_reposted_to_naver, ~has_earlier_naver_twin)


@router.get("/posts")
async def list_public_posts(
    source: Literal["brunch", "naver"] | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(12, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    query = select(Post).where(_dedupe_by_title()).order_by(Post.scraped_at.desc())
    count_query = select(func.count(Post.id)).where(_dedupe_by_title())
    if source:
        query = query.where(Post.source == source)
        count_query = count_query.where(Post.source == source)

    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    posts = result.scalars().all()

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
                "thumbnail": p.thumbnail,
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
        "thumbnail": post.thumbnail,
        "images": post.images,
        "scraped_at": str(post.scraped_at) if post.scraped_at else None,
    }
