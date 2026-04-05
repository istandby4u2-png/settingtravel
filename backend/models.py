from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, UniqueConstraint
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
    """Google Sites Booklog / 장르·도서 목에서 이전한 독서 기록."""

    __tablename__ = "booklog_entries"
    __table_args__ = (UniqueConstraint("year", "title", name="uq_booklog_year_title"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    year = Column(Integer, nullable=True)  # 2010–2017 등, 미구분이면 null
    title = Column(String(500), nullable=False)
    author = Column(String(300), nullable=True)
    note = Column(Text, nullable=True)
    source_url = Column(String(1200), nullable=True, unique=True)
    sort_order = Column(Integer, default=0)
    imported_at = Column(DateTime, server_default=func.now())
