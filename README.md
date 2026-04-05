# 배경여행 - 블로그 문체 분석 & 자동 생성 서비스

브런치(brunch.co.kr)와 네이버 블로그(blog.naver.com)에 업로드된 글을 자동으로 수집하여 문체를 분석하고, Google Gemini AI를 활용해 동일한 스타일의 새로운 블로그 글을 자동 생성하는 웹 서비스입니다.

## 기능

- **블로그 스크래핑**: 브런치와 네이버 블로그에서 모든 글을 자동 수집
- **문체 분석**: 통계적 분석(문장 길이, 종결어미, 빈출 어휘 등) + AI 정성 분석(톤, 서술 방식, 수사법 등)
- **글 자동 생성**: 분석된 문체로 주제만 입력하면 블로그 글을 AI가 작성
- **생성 히스토리**: 생성된 글의 저장 및 관리

## 기술 스택

- **Backend**: Python, FastAPI, SQLAlchemy, Playwright, SQLite
- **Frontend**: Next.js 16, TypeScript, Tailwind CSS, shadcn/ui
- **AI**: Google Gemini API (gemini-2.0-flash)

## 시작하기

### 사전 준비

- Python 3.11 이상
- Node.js 18 이상
- Google Gemini API 키 ([aistudio.google.com](https://aistudio.google.com)에서 무료 발급)

### 1. API 키 설정

```bash
# backend/.env 파일을 열어서 API 키를 입력하세요
GOOGLE_API_KEY=여기에_실제_API_키_입력
```

### 2. 백엔드 실행

```bash
cd backend
pip install -r requirements.txt
playwright install chromium
uvicorn main:app --reload
```

백엔드가 `http://localhost:8000`에서 실행됩니다.

### 3. 프론트엔드 실행

```bash
cd frontend
npm install
npm run dev
```

프론트엔드가 `http://localhost:3000`에서 실행됩니다.

### 4. 사용 순서

1. **스크래핑**: "스크래핑" 페이지에서 "스크래핑 시작" 버튼 클릭 → 브런치/네이버 블로그 글 수집
2. **분석**: "문체 분석" 페이지에서 "분석 실행" 클릭 → 통계+AI 문체 분석
3. **생성**: "글 생성" 페이지에서 주제 입력 → 분석된 스타일로 새 글 생성

## 프로젝트 구조

```
배경여행/
├── backend/
│   ├── main.py              # FastAPI 앱
│   ├── database.py          # DB 설정
│   ├── models.py            # DB 모델
│   ├── scrapers/            # 스크래퍼 모듈
│   │   ├── brunch_scraper.py
│   │   └── naver_scraper.py
│   ├── analyzer/            # 문체 분석기
│   │   └── style_analyzer.py
│   ├── generator/           # 글 생성기
│   │   └── blog_generator.py
│   └── routers/             # API 엔드포인트
│       ├── scrape.py
│       ├── analyze.py
│       └── generate.py
├── frontend/
│   └── src/
│       ├── app/             # Next.js 페이지
│       ├── components/      # UI 컴포넌트
│       └── lib/api.ts       # API 클라이언트
└── README.md
```

## API 엔드포인트

| Method | Path | 설명 |
|--------|------|------|
| GET | `/api/health` | 서버 상태 확인 |
| POST | `/api/scrape/start` | 스크래핑 시작 (대시보드·수동) |
| POST | `/api/scrape/cron` | 스케줄용 스크래핑 시작 (`CRON_SECRET` + `Authorization: Bearer …` 또는 `X-Cron-Secret`) |
| GET | `/api/scrape/status` | 스크래핑 상태 조회 |
| GET | `/api/scrape/posts` | 수집된 글 목록 |
| POST | `/api/analyze/run` | 문체 분석 실행 |
| GET | `/api/analyze/latest` | 최신 분석 결과 |
| POST | `/api/generate/create` | 블로그 글 생성 |
| GET | `/api/generate/history` | 생성 히스토리 |

## 자동 아카이브 (스케줄)

프론트의 `/blog`는 API의 `GET /api/blog/posts`로 DB에 쌓인 글을 보여 줍니다. 새 글을 주기적으로 반영하려면 백엔드에 `CRON_SECRET`을 넣고, 스케줄러가 `POST /api/scrape/cron`을 호출하면 됩니다.

1. **Fly.io (또는 호스팅) 시크릿**: `CRON_SECRET`을 임의의 긴 문자열로 설정합니다.  
   `fly secrets set CRON_SECRET='...'`
2. **GitHub Actions** (이 저장소에 `.github/workflows/scheduled-blog-archive.yml` 포함):  
   Repository secrets에 `BACKEND_API_URL`(예: `https://your-app.fly.dev`), `CRON_SECRET`(위와 동일)을 추가합니다.  
   매일 실행되며, 필요하면 Actions에서 **Run workflow**로 수동 실행할 수 있습니다.
3. **다른 서비스** (cron-job.org 등): 동일 URL로 `POST`, 헤더 `Authorization: Bearer <CRON_SECRET>`.

`CRON_SECRET`이 비어 있으면 `/api/scrape/cron`은 503을 반환합니다.

## 참고사항

- 스크래핑은 브런치/네이버 블로그의 HTML 구조에 의존하므로, 사이트 구조 변경 시 스크래퍼 업데이트가 필요할 수 있습니다.
- Gemini API 무료 티어에는 분당 요청 수 제한이 있습니다.
- 스크래핑 시 서버에 부하를 주지 않기 위해 요청 사이에 자동으로 딜레이가 적용됩니다.
