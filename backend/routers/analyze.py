from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import json

from database import get_db
from models import Post, StyleAnalysis
from analyzer.style_analyzer import statistical_analysis, ai_analysis, full_analysis

router = APIRouter()


@router.post("/run")
async def run_analysis(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Post))
    posts = result.scalars().all()

    if not posts:
        return {"error": "분석할 글이 없습니다. 먼저 스크래핑을 실행해주세요."}

    post_dicts = [
        {"title": p.title, "content": p.content, "source": p.source}
        for p in posts
    ]

    analysis_result = await full_analysis(post_dicts)

    record = StyleAnalysis(analysis_json=analysis_result)
    db.add(record)
    await db.commit()
    await db.refresh(record)

    return {
        "id": record.id,
        "analysis": analysis_result,
        "created_at": str(record.created_at) if record.created_at else None,
    }


@router.get("/latest")
async def get_latest_analysis(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(StyleAnalysis).order_by(StyleAnalysis.created_at.desc()).limit(1)
    )
    record = result.scalar_one_or_none()

    if not record:
        return {"error": "분석 결과가 없습니다. 먼저 분석을 실행해주세요."}

    return {
        "id": record.id,
        "analysis": record.analysis_json,
        "created_at": str(record.created_at) if record.created_at else None,
    }


@router.get("/history")
async def get_analysis_history(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(StyleAnalysis).order_by(StyleAnalysis.created_at.desc()).limit(10)
    )
    records = result.scalars().all()

    return {
        "analyses": [
            {
                "id": r.id,
                "created_at": str(r.created_at) if r.created_at else None,
                "total_posts": r.analysis_json.get("statistical", {}).get("total_posts", 0)
                if isinstance(r.analysis_json, dict) else 0,
            }
            for r in records
        ]
    }


@router.post("/statistical-only")
async def run_statistical_only(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Post))
    posts = result.scalars().all()

    if not posts:
        return {"error": "분석할 글이 없습니다."}

    post_dicts = [{"title": p.title, "content": p.content} for p in posts]
    stats = statistical_analysis(post_dicts)

    return {"statistical": stats}
