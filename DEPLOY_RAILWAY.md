# Railway 배포 가이드

## 사전 준비

1. [Railway](https://railway.app) 가입 (GitHub 계정으로)
2. 이 레포를 GitHub에 push
3. [data.go.kr](https://www.data.go.kr) API 키 발급

## 배포 순서 (10분)

### 1. Railway 프로젝트 생성

```
railway.app → New Project → Empty Project
```

### 2. PostgreSQL 추가

```
프로젝트 대시보드 → "+ New" → Database → PostgreSQL
```

생성 후 `DATABASE_URL` 값을 Variables 탭에서 확인해둡니다.

### 3. 백엔드 서비스 추가

```
"+ New" → GitHub Repo → 이 레포 선택
```

설정:
- **Root Directory**: `backend`
- **Variables** (Add Variable):

| 변수명 | 값 |
|--------|-----|
| `DATABASE_URL` | PostgreSQL 서비스의 `DATABASE_URL` 참조 (`${{Postgres.DATABASE_URL}}` 로 자동 연결) |
| `ENV` | `development` (프로토타입), `production` (실서비스) |
| `SECRET_KEY` | 아무 32자 이상 문자열 (예: `openssl rand -hex 32` 로 생성) |
| `CORS_ORIGINS` | 4단계에서 생성되는 프론트엔드 URL (나중에 수정) |
| `DATA_GO_KR_API_KEY` | data.go.kr에서 발급받은 키 |

> `DATABASE_URL` 주의: Railway PostgreSQL은 `postgresql://` 형식이므로, 
> `SQLALCHEMY_DATABASE_URL`로 `postgresql+asyncpg://` 형식으로 변환 필요.
> 
> 방법: `DATABASE_URL` 값을 복사한 뒤, `postgresql://` → `postgresql+asyncpg://` 로 바꿔서 입력

Deploy 클릭 → 빌드 완료 대기

**도메인 생성**: Settings → Networking → Generate Domain  
→ 예: `searchpro-api-production.up.railway.app`

### 4. 프론트엔드 서비스 추가

```
"+ New" → GitHub Repo → 같은 레포 선택
```

설정:
- **Root Directory**: `frontend`
- **Variables**:

| 변수명 | 값 |
|--------|-----|
| `NEXT_PUBLIC_API_URL` | 3단계 백엔드 도메인 (예: `https://searchpro-api-production.up.railway.app`) |
| `NEXT_PUBLIC_SITE_URL` | 이 서비스의 도메인 (Deploy 후 생성) |
| `NEXTAUTH_URL` | `NEXT_PUBLIC_SITE_URL`과 동일 |
| `NEXTAUTH_SECRET` | 32자 이상 랜덤 문자열 |

Deploy 클릭 → 빌드 완료 대기

**도메인 생성**: Settings → Networking → Generate Domain  
→ 예: `searchpro-production.up.railway.app`

### 5. CORS 업데이트

백엔드 서비스 Variables에서:
```
CORS_ORIGINS=https://searchpro-production.up.railway.app
```

### 6. 확인

- 프론트엔드: `https://searchpro-production.up.railway.app`
- 백엔드 API: `https://searchpro-api-production.up.railway.app/health`
- API 문서: `https://searchpro-api-production.up.railway.app/docs` (development 모드일 때만)

## 선택 환경변수 (나중에 추가)

| 변수명 | 용도 |
|--------|------|
| `OPENAI_API_KEY` | AI 공고 요약 |
| `ANTHROPIC_API_KEY` | AI 요약 폴백 |
| `RESEND_API_KEY` | 이메일 알림 |
| `KAKAO_CLIENT_ID` | 카카오 로그인 |
| `KAKAO_CLIENT_SECRET` | 카카오 로그인 |
| `ADMIN_EMAILS` | 관리자 이메일 (쉼표 구분) |

## 커스텀 도메인 (선택)

Railway Settings → Networking → Custom Domain:
```
api.searchpro.kr → 백엔드
searchpro.kr → 프론트엔드
```

DNS 설정: CNAME 레코드 추가 (Railway가 안내해줌)

## 비용

Railway 무료 플랜:
- 월 $5 크레딧 (Trial)
- 500시간 실행 시간
- 1GB 메모리

프로토타입 단계에서는 무료로 충분합니다.  
Hobby 플랜($5/월)으로 업그레이드하면 제한 없이 사용 가능합니다.

## 트러블슈팅

### 백엔드 빌드 실패
- Railway Logs 탭에서 에러 확인
- `DATABASE_URL` 형식이 `postgresql+asyncpg://`인지 확인

### 프론트엔드 빌드 실패
- `NEXT_PUBLIC_API_URL`이 설정되어 있는지 확인
- Build Logs에서 TypeScript 에러 확인

### DB 마이그레이션
- 백엔드 `railway.toml`의 `startCommand`에 `alembic upgrade head`가 포함되어 있어 자동 실행됨
