# SearchPro — 정부지원사업 통합 검색 플랫폼

정부지원사업, 공모전, 보조금 정보를 한곳에서 검색하고 관리하는 통합 플랫폼입니다.

## 프로젝트 구조

```
searchpro/
├── frontend/          # Next.js 14+ (App Router, TypeScript)
├── backend/           # FastAPI (Python)
├── shared/            # 공유 타입 정의
├── scripts/           # 유틸리티 스크립트
├── docker-compose.yml # 로컬 개발용
└── .env.example       # 환경변수 템플릿
```

## 기술 스택

### Frontend
- Next.js 14+ (App Router)
- TypeScript
- Tailwind CSS 4
- shadcn/ui
- Zustand (전역 상태)
- TanStack React Query (서버 상태)
- next-auth (인증)
- lucide-react (아이콘)
- date-fns (날짜 처리)

### Backend
- FastAPI + Uvicorn
- SQLAlchemy 2.0 (async) + Alembic
- Pydantic v2
- PostgreSQL (asyncpg)
- httpx (비동기 HTTP)
- APScheduler (스케줄링)

## 로컬 개발 환경 설정

### 1. 환경변수 설정

```bash
cp .env.example .env
# .env 파일을 열어 필요한 값 입력
```

### 2. Docker로 백엔드 + DB 실행

```bash
docker-compose up
```

- PostgreSQL: `localhost:5432` (DB: govfinder)
- Backend API: `http://localhost:8000`
- Health check: `http://localhost:8000/health`
- API docs: `http://localhost:8000/docs`

### 3. 프론트엔드 실행

```bash
cd frontend
npm install
npm run dev
```

- Frontend: `http://localhost:3000`

## API 문서

FastAPI 자동 생성 문서:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
