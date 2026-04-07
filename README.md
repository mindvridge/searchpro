# SearchPro — 정부지원사업 통합 검색 플랫폼

정부지원사업, 공모전, 보조금 정보를 한곳에서 검색하고, AI 맞춤 추천과 마감 알림을 받을 수 있는 통합 플랫폼입니다.

## 주요 기능

- **통합 검색** — 기업마당, K-Startup, 씽굿, 위비티 등 5개 소스 통합
- **고급 필터** — 카테고리, 지역, 금액, 마감일, 상태별 필터링 + facet 카운트
- **AI 요약** — GPT-4o-mini / Claude Haiku로 공고문 구조화 요약
- **맞춤 추천** — 사용자 프로필 기반 규칙 엔진 추천
- **마감 캘린더** — 월간 뷰로 마감일 한눈에 확인
- **알림 시스템** — 키워드/카테고리/마감일 기반 이메일 알림
- **북마크** — 관심 사업 저장 + 메모
- **관리자 대시보드** — 크롤러 관리, 통계 차트, 사용자/공고 관리

## 기술 스택

### Frontend
| 기술 | 용도 |
|------|------|
| Next.js 16 (App Router) | 프레임워크 |
| TypeScript | 타입 안전성 |
| Tailwind CSS 4 | 스타일링 |
| shadcn/ui (base-ui) | UI 컴포넌트 |
| NextAuth.js v5 | 인증 (이메일 + 카카오) |
| TanStack React Query | 서버 상태 관리 |
| Zustand | 클라이언트 상태 |
| recharts | 관리자 차트 |
| date-fns | 날짜 처리 |

### Backend
| 기술 | 용도 |
|------|------|
| FastAPI | API 프레임워크 |
| SQLAlchemy 2.0 (async) | ORM |
| Alembic | DB 마이그레이션 |
| PostgreSQL 16 | 데이터베이스 |
| asyncpg | 비동기 PG 드라이버 |
| APScheduler | 크롤링/알림 스케줄러 |
| httpx | 비동기 HTTP |
| BeautifulSoup4 | 웹 크롤링 |
| joserfc | JWT 인증 |
| cachetools | 인메모리 캐시 |

## 프로젝트 구조

```
searchpro/
├── frontend/                    # Next.js 16 App
│   ├── src/
│   │   ├── app/                 # 16개 라우트
│   │   │   ├── admin/           # 관리자 대시보드 (4페이지)
│   │   │   ├── alerts/          # 알림 설정
│   │   │   ├── calendar/        # 마감 캘린더
│   │   │   ├── login/           # 로그인
│   │   │   ├── register/        # 회원가입
│   │   │   ├── onboarding/      # 프로필 설정
│   │   │   ├── programs/        # 공고 목록 + 상세
│   │   │   └── page.tsx         # 메인 (랜딩/대시보드)
│   │   ├── components/          # 공유 컴포넌트
│   │   ├── hooks/               # React Query 훅
│   │   └── lib/                 # 유틸리티
│   └── vercel.json
├── backend/                     # FastAPI
│   ├── app/
│   │   ├── api/v1/endpoints/    # 8개 엔드포인트 모듈
│   │   ├── core/                # 인증, 스케줄러
│   │   ├── crawlers/            # 5개 크롤러
│   │   ├── models/              # 6개 SQLAlchemy 모델
│   │   ├── schemas/             # Pydantic 스키마
│   │   └── services/            # AI, 알림, 추천, 크롤러
│   ├── alembic/                 # DB 마이그레이션
│   ├── Dockerfile               # 멀티스테이지 빌드
│   └── Procfile                 # Railway/Heroku
├── shared/                      # 공유 타입
├── scripts/                     # 유틸리티 스크립트
├── docker-compose.yml           # 로컬 개발
├── docker-compose.prod.yml      # 프로덕션
└── .env.example                 # 환경변수 템플릿
```

## 로컬 개발 환경 설정

### 사전 요구사항
- Node.js 20+
- Python 3.11+
- Docker & Docker Compose

### 1. 환경변수 설정

```bash
cp .env.example .env
# .env 파일을 열어 필요한 값 입력
```

### 2. 백엔드 + DB 실행 (Docker)

```bash
docker-compose up -d
```

- PostgreSQL: `localhost:5432` (DB: govfinder)
- Backend API: `http://localhost:8000`
- API 문서: `http://localhost:8000/docs`

### 3. DB 마이그레이션

```bash
cd backend
pip install -r requirements.txt
alembic upgrade head
```

### 4. 프론트엔드 실행

```bash
cd frontend
npm install
npm run dev
```

- Frontend: `http://localhost:3000`

## 환경변수 발급 가이드

### data.go.kr API 키 (필수)
1. [공공데이터포털](https://www.data.go.kr) 회원가입
2. "중소기업 지원사업 통합공고 조회" API 활용 신청
3. 발급된 인증키를 `DATA_GO_KR_API_KEY`에 입력

### 카카오 로그인 (선택)
1. [카카오 개발자](https://developers.kakao.com) 앱 생성
2. 카카오 로그인 활성화, Redirect URI 설정
3. REST API 키 → `KAKAO_CLIENT_ID`, 보안키 → `KAKAO_CLIENT_SECRET`

### OpenAI API (선택 — AI 요약용)
1. [OpenAI Platform](https://platform.openai.com/api-keys)에서 API 키 발급
2. `OPENAI_API_KEY`에 입력

### Resend (선택 — 이메일 알림용)
1. [Resend](https://resend.com) 가입, API 키 발급
2. `RESEND_API_KEY`에 입력

## 배포 가이드

### 프론트엔드 — Vercel

```bash
# Vercel CLI
npx vercel --prod
```

환경변수 설정:
- `NEXT_PUBLIC_API_URL` = 백엔드 URL
- `NEXT_PUBLIC_SITE_URL` = 프론트엔드 URL
- `NEXTAUTH_URL` = 프론트엔드 URL
- `NEXTAUTH_SECRET` = 32자 이상 랜덤 문자열
- `KAKAO_CLIENT_ID`, `KAKAO_CLIENT_SECRET`
- `NEXT_PUBLIC_ADMIN_EMAILS`

### 백엔드 — Railway

1. Railway 프로젝트 생성 → PostgreSQL 애드온 추가
2. GitHub 레포 연결, `backend/` 루트 디렉토리 설정
3. 환경변수: `DATABASE_URL`, `SECRET_KEY`, `ENV=production`, `CORS_ORIGINS`

### 도메인 설정

1. Cloudflare DNS에 도메인 추가
2. Vercel: 프로젝트 Settings → Domains → 커스텀 도메인 추가
3. Railway: Settings → Networking → Custom Domain
4. SSL은 Vercel + Cloudflare에서 자동 처리

## API 크롤링 스케줄

| 소스 | 스케줄 (KST) | 방식 |
|------|-------------|------|
| 기업마당 | 06:00, 18:00 | 공공데이터 API |
| K-Startup | 07:00, 19:00 | 공공데이터 API |
| 씽굿 | 12:00 | 웹 크롤링 |
| 위비티 | 12:30 | 웹 크롤링 |
| 마감 갱신 | 00:05 | DB 업데이트 |
| 마감 알림 | 09:00 | 이메일 발송 |

## 보안

- JWT (HS256) + HTTPOnly Cookie 인증
- PBKDF2-SHA256 비밀번호 해싱 (260,000 iterations)
- Rate Limiting: 인증 10/min, 검색 30/min, 일반 100/min
- CORS: 허용 도메인만 (환경변수)
- Security Headers: HSTS, X-Frame-Options, CSP
- SQLAlchemy ORM으로 SQL Injection 방지
- Next.js 기본 XSS 이스케이핑

## 라이선스

MIT License
