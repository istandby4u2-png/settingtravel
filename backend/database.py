from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
import os

DATA_DIR = os.environ.get("DATA_DIR", os.path.dirname(__file__))
DB_PATH = os.path.join(DATA_DIR, "blog_service.db")
DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


_MIGRATIONS: list[tuple[str, str, str]] = [
    # (table, column, type)
    ("posts", "thumbnail", "VARCHAR(2000)"),
    ("posts", "images", "TEXT"),
    ("booklog_entries", "translator", "VARCHAR(300)"),
    ("booklog_entries", "publisher", "VARCHAR(300)"),
    ("booklog_entries", "published", "VARCHAR(20)"),
    ("booklog_entries", "purchase_date", "VARCHAR(20)"),
    ("booklog_entries", "isbn", "VARCHAR(20)"),
    ("booklog_entries", "cover_url", "VARCHAR(1200)"),
    ("booklog_entries", "source", "VARCHAR(30)"),
    ("booklog_entries", "source_ref", "VARCHAR(200)"),
]


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # lightweight migration: add columns if missing (SQLite)
        from sqlalchemy import text

        for table, col, typedef in _MIGRATIONS:
            try:
                await conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {typedef}"))
            except Exception:
                pass


async def get_db():
    async with async_session() as session:
        yield session
