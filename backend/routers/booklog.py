"""Booklog 공개 API (DB booklog_entries)."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import BooklogEntry

router = APIRouter()


@router.get("/years")
async def list_years(db: AsyncSession = Depends(get_db)):
    q = select(BooklogEntry.year).distinct()
    result = await db.execute(q)
    raw = [r[0] for r in result.all()]
    has_unassigned = None in raw
    years_sorted = sorted([y for y in raw if y is not None], reverse=True)
    return {"years": years_sorted, "has_unassigned": has_unassigned}


@router.get("/items")
async def list_items(
    year: int | None = Query(None, description="특정 연도만"),
    unassigned: bool = Query(False, description="연도 미지정 항목만"),
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=300),
    db: AsyncSession = Depends(get_db),
):
    query = select(BooklogEntry).order_by(
        BooklogEntry.year.desc().nulls_last(),
        BooklogEntry.sort_order,
        BooklogEntry.id,
    )
    count_q = select(func.count(BooklogEntry.id))

    if unassigned:
        query = query.where(BooklogEntry.year.is_(None))
        count_q = count_q.where(BooklogEntry.year.is_(None))
    elif year is not None:
        query = query.where(BooklogEntry.year == year)
        count_q = count_q.where(BooklogEntry.year == year)

    total = (await db.execute(count_q)).scalar() or 0
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)
    rows = (await db.execute(query)).scalars().all()

    return {
        "items": [
            {
                "id": r.id,
                "year": r.year,
                "title": r.title,
                "author": r.author,
                "note": r.note,
                "source_url": r.source_url,
            }
            for r in rows
        ],
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.get("/items/{entry_id}")
async def get_item(entry_id: int, db: AsyncSession = Depends(get_db)):
    r = await db.get(BooklogEntry, entry_id)
    if not r:
        raise HTTPException(404, detail="항목을 찾을 수 없습니다.")
    return {
        "id": r.id,
        "year": r.year,
        "title": r.title,
        "author": r.author,
        "note": r.note,
        "source_url": r.source_url,
    }
