#!/usr/bin/env python3
"""booklog_entries 테이블에 시드 데이터 삽입 (중복 year+title 은 건너뜀)."""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select

from data.booklog_seed_data import BOOKS, YEARS_CYCLE
from database import async_session, init_db
from models import BooklogEntry


async def main() -> None:
    await init_db()
    inserted = 0
    skipped = 0
    async with async_session() as session:
        for i, row in enumerate(BOOKS):
            title = (row["title"] or "")[:500]
            author = row.get("author")
            if author:
                author = author[:300]
            year = YEARS_CYCLE[i % len(YEARS_CYCLE)]
            sort_order = i
            existing = await session.execute(
                select(BooklogEntry.id).where(
                    BooklogEntry.year == year,
                    BooklogEntry.title == title,
                )
            )
            if existing.scalar_one_or_none() is not None:
                skipped += 1
                continue
            session.add(
                BooklogEntry(
                    year=year,
                    title=title,
                    author=author,
                    note="Google Sites 공개 목차(Genre·book) 기반 시드. 연도는 순환 배치(추정).",
                    sort_order=sort_order,
                )
            )
            inserted += 1
        await session.commit()

    print(f"Booklog 시드 완료: 신규 {inserted}건, 건너뜀 {skipped}건")


if __name__ == "__main__":
    asyncio.run(main())
