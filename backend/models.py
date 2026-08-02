from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from database import Base


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(20), nullable=False)  # "brunch" or "naver"
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    url = Column(String(1000), unique=True, nullable=False)
    published_date = Column(String(50))
    thumbnail = Column(String(2000), nullable=True)
    images = Column(JSON, nullable=True)
    scraped_at = Column(DateTime, server_default=func.now())


class StyleAnalysis(Base):
    __tablename__ = "style_analysis"

    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_json = Column(JSON, nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class GeneratedPost(Base):
    __tablename__ = "generated_posts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    topic = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    style_profile_id = Column(Integer, ForeignKey("style_analysis.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class BooklogEntry(Base):
    """구매 도서 아카이브. Google Sites Booklog(2010–2017)와 교보문고 주문내역에서 이전."""

    __tablename__ = "booklog_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    year = Column(Integer, nullable=True, index=True)  # 구매 연도, 미구분이면 null
    title = Column(String(500), nullable=False)
    author = Column(String(300), nullable=True)
    translator = Column(String(300), nullable=True)
    publisher = Column(String(300), nullable=True)
    published = Column(String(20), nullable=True)  # 출판년월 "YYYY-MM-DD" / "YYYY-MM"
    purchase_date = Column(String(20), nullable=True)  # "YYYY-MM-DD" / "YYYY-MM"
    isbn = Column(String(20), nullable=True)
    cover_url = Column(String(1200), nullable=True)
    note = Column(Text, nullable=True)
    source = Column(String(30), nullable=True, index=True)  # "google_sites" | "kyobo"
    source_url = Column(String(1200), nullable=True)
    # 재임포트 시 중복 방지용 안정 키 (예: "google_sites:2010:1")
    source_ref = Column(String(200), nullable=True, unique=True)
    sort_order = Column(Integer, default=0)
    imported_at = Column(DateTime, server_default=func.now())
