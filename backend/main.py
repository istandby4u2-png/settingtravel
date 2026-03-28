import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from routers import scrape, analyze, generate, auth, photos, blog, booklog

load_dotenv()

_cors_origins = ["http://localhost:3000"]
_extra = os.getenv("CORS_EXTRA_ORIGINS", "")
if _extra.strip():
    _cors_origins.extend(o.strip() for o in _extra.split(",") if o.strip())


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="블로그 문체 분석 & 자동 생성 서비스", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scrape.router, prefix="/api/scrape", tags=["scrape"])
app.include_router(blog.router, prefix="/api/blog", tags=["blog"])
app.include_router(booklog.router, prefix="/api/booklog", tags=["booklog"])
app.include_router(analyze.router, prefix="/api/analyze", tags=["analyze"])
app.include_router(generate.router, prefix="/api/generate", tags=["generate"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(photos.router, prefix="/api/photos", tags=["photos"])


@app.get("/api/health")
async def health():
    return {"status": "ok"}
