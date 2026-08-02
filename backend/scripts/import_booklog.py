#!/usr/bin/env python3
"""구매 도서 아카이브를 booklog_entries 테이블에 적재한다.

데이터 원본: backend/data/booklog_purchases.json
  - google_sites: Google Sites Booklog 2010–2017 연도별 구매 내역 표
  - kyobo: 교보문고 주문내역

source_ref 기준으로 upsert 하므로 반복 실행해도 안전하다.
--rebuild 를 주면 테이블을 새로 만들어 과거 시드(연도 추정값)를 완전히 걷어낸다.
"""

import argparse
import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, text

from database import async_session, engine, init_db
from models import Base, BooklogEntry

DATA_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "booklog_purchases.json",
)

FIELDS = (
    "year",
    "title",
    "author",
    "translator",
    "publisher",
    "published",
    "purchase_date",
    "isbn",
    "cover_url",
    "note",
    "source",
    "source_url",
    "sort_order",
)


async def rebuild_table() -> None:
    """구 스키마의 유니크 제약(year+title, source_url)을 버리기 위해 테이블을 다시 만든다."""
    async with engine.begin() as conn:
        await conn.execute(text("DROP TABLE IF EXISTS booklog_entries"))
        await conn.run_sync(Base.metadata.create_all)


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="기존 booklog_entries 를 비우고 새 스키마로 다시 만든다",
    )
    parser.add_argument("--file", default=DATA_FILE)
    args = parser.parse_args()

    with open(args.file, encoding="utf-8") as f:
        records = json.load(f)

    if args.rebuild:
        await rebuild_table()
    else:
        await init_db()

    inserted = updated = 0
    async with async_session() as session:
        existing = {
            ref: eid
            for eid, ref in (
                await session.execute(
                    select(BooklogEntry.id, BooklogEntry.source_ref).where(
                        BooklogEntry.source_ref.is_not(None)
                    )
                )
            ).all()
        }

        for rec in records:
            ref = rec.get("source_ref")
            values = {k: rec.get(k) for k in FIELDS}
            entry_id = existing.get(ref) if ref else None
            if entry_id is not None:
                entry = await session.get(BooklogEntry, entry_id)
                for k, v in values.items():
                    setattr(entry, k, v)
                updated += 1
            else:
                session.add(BooklogEntry(source_ref=ref, **values))
                inserted += 1

        await session.commit()

        total = len((await session.execute(select(BooklogEntry.id))).all())

    print(f"임포트 완료: 신규 {inserted}건, 갱신 {updated}건 (테이블 총 {total}건)")


if __name__ == "__main__":
    asyncio.run(main())
