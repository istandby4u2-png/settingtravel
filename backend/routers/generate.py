from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from models import StyleAnalysis, GeneratedPost
from generator.blog_generator import generate_blog_post
from utils.url_fetcher import fetch_url_content

router = APIRouter()


class GenerateRequest(BaseModel):
    topic: str
    length: str = "medium"
    additional_instructions: str = ""
    reference_url: str = ""


@router.post("/create")
async def create_post(req: GenerateRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(StyleAnalysis).order_by(StyleAnalysis.created_at.desc()).limit(1)
    )
    style_record = result.scalar_one_or_none()

    if not style_record:
        return {"error": "스타일 분석 결과가 없습니다. 먼저 문체 분석을 실행해주세요."}

    style_profile = style_record.analysis_json

    reference_text = ""
    if req.reference_url.strip():
        print(f"[generate] Fetching reference URL: {req.reference_url}", flush=True)
        ref_result = await fetch_url_content(req.reference_url)
        if "error" in ref_result:
            return {"error": f"참조 URL 가져오기 실패: {ref_result['error']}"}
        reference_text = ref_result["content"]
        print(f"[generate] Reference content: {len(reference_text)} chars", flush=True)

    generated = await generate_blog_post(
        topic=req.topic,
        style_profile=style_profile,
        length=req.length,
        additional_instructions=req.additional_instructions,
        reference_text=reference_text,
        reference_url=req.reference_url.strip(),
    )

    if "error" in generated:
        return generated

    record = GeneratedPost(
        topic=req.topic,
        content=f"# {generated['title']}\n\n{generated['content']}",
        style_profile_id=style_record.id,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    return {
        "id": record.id,
        "title": generated["title"],
        "content": generated["content"],
        "topic": req.topic,
        "length": req.length,
        "char_count": generated.get("char_count", 0),
        "reference_url": req.reference_url.strip() or None,
        "created_at": str(record.created_at) if record.created_at else None,
    }


@router.get("/history")
async def get_generation_history(
    page: int = 1,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * limit
    result = await db.execute(
        select(GeneratedPost)
        .order_by(GeneratedPost.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    posts = result.scalars().all()

    return {
        "posts": [
            {
                "id": p.id,
                "topic": p.topic,
                "content": p.content[:300] + "..." if len(p.content) > 300 else p.content,
                "created_at": str(p.created_at) if p.created_at else None,
            }
            for p in posts
        ]
    }


@router.get("/history/{post_id}")
async def get_generated_post(post_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(GeneratedPost).where(GeneratedPost.id == post_id)
    )
    post = result.scalar_one_or_none()

    if not post:
        return {"error": "글을 찾을 수 없습니다."}

    return {
        "id": post.id,
        "topic": post.topic,
        "content": post.content,
        "created_at": str(post.created_at) if post.created_at else None,
    }
