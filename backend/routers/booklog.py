"""Booklog 공개 API (DB booklog_entries)."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import BooklogEntry

router = APIRouter()


def serialize(r: BooklogEntry) -> dict:
    return {
        "id": r.id,
        "year": r.year,
        "title": r.title,
        "author": r.author,
        "translator": r.translator,
        "publisher": r.publisher,
        "published": r.published,
        "purchase_date": r.purchase_date,
        "isbn": r.isbn,
        "cover_url": r.cover_url,
        "note": r.note,
        "source": r.source,
        "source_url": r.source_url,
    }


@router.get("/years")
async def list_years(db: AsyncSession = Depends(get_db)):
    q = select(BooklogEntry.year, func.count(BooklogEntry.id)).group_by(BooklogEntry.year)
    rows = (await db.execute(q)).all()
    counts = {y: c for y, c in rows if y is not None}
    has_unassigned = any(y is None for y, _ in rows)
    years_sorted = sorted(counts, reverse=True)
    return {
        "years": years_sorted,
        "counts": counts,
        "has_unassigned": has_unassigned,
        "total": sum(c for _, c in rows),
    }


@router.get("/items")
async def list_items(
    year: int | None = Query(None, description="특정 연도만"),
    unassigned: bool = Query(False, description="연도 미지정 항목만"),
    source: str | None = Query(None, description="google_sites | kyobo"),
    q: str | None = Query(None, description="제목·저자·출판사 검색어"),
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=300),
    db: AsyncSession = Depends(get_db),
):
    query = select(BooklogEntry)
    count_q = select(func.count(BooklogEntry.id))

    filters = []
    if unassigned:
        filters.append(BooklogEntry.year.is_(None))
    elif year is not None:
        filters.append(BooklogEntry.year == year)
    if source:
        filters.append(BooklogEntry.source == source)
    if q:
        like = f"%{q.strip()}%"
        filters.append(
            or_(
                BooklogEntry.title.ilike(like),
                BooklogEntry.author.ilike(like),
                BooklogEntry.publisher.ilike(like),
            )
        )
    for f in filters:
        query = query.where(f)
        count_q = count_q.where(f)

    total = (await db.execute(count_q)).scalar() or 0
    rows = (
        await db.execute(
            query.order_by(
                BooklogEntry.year.desc().nulls_last(),
                BooklogEntry.purchase_date.desc().nulls_last(),
                BooklogEntry.sort_order,
                BooklogEntry.id,
            )
            .offset((page - 1) * limit)
            .limit(limit)
        )
    ).scalars().all()

    return {
        "items": [serialize(r) for r in rows],
        "total": total,
        "page": page,
        "limit": limit,
        "has_more": page * limit < total,
    }


@router.get("/items/{entry_id}")
async def get_item(entry_id: int, db: AsyncSession = Depends(get_db)):
    r = await db.get(BooklogEntry, entry_id)
    if not r:
        raise HTTPException(404, detail="항목을 찾을 수 없습니다.")
    return serialize(r)
