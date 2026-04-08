#!/bin/bash
# SearchPro 로컬 개발 서버
#
# 사용법:
#   ./scripts/dev.sh        # DB + 백엔드 + 프론트엔드 한번에 실행
#   ./scripts/dev.sh db     # DB만 실행
#   ./scripts/dev.sh back   # 백엔드만 실행
#   ./scripts/dev.sh front  # 프론트엔드만 실행
#   ./scripts/dev.sh stop   # DB 컨테이너 종료

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

DB_CONTAINER="searchpro-pg"

start_db() {
    if docker ps --format '{{.Names}}' | grep -q "^${DB_CONTAINER}$"; then
        echo -e "${GREEN}  DB 이미 실행중${NC}"
        return
    fi

    if docker ps -a --format '{{.Names}}' | grep -q "^${DB_CONTAINER}$"; then
        echo -e "${YELLOW}  DB 컨테이너 재시작...${NC}"
        docker start "$DB_CONTAINER" > /dev/null
    else
        echo -e "${YELLOW}  DB 컨테이너 생성...${NC}"
        docker run -d \
            --name "$DB_CONTAINER" \
            -e POSTGRES_DB=govfinder \
            -e POSTGRES_USER=postgres \
            -e POSTGRES_PASSWORD=postgres \
            -p 5432:5432 \
            -v "${PROJECT_ROOT}/docker/pgdata:/var/lib/postgresql/data" \
            postgres:16 > /dev/null
    fi

    echo -e "${YELLOW}  DB 준비 대기중...${NC}"
    for i in $(seq 1 30); do
        if docker exec "$DB_CONTAINER" pg_isready -U postgres > /dev/null 2>&1; then
            # pg_trgm 확장 활성화
            docker exec "$DB_CONTAINER" psql -U postgres -d govfinder -c "CREATE EXTENSION IF NOT EXISTS pg_trgm;" > /dev/null 2>&1
            echo -e "${GREEN}  DB 준비 완료 (localhost:5432)${NC}"
            return
        fi
        sleep 1
    done
    echo -e "${RED}  DB 시작 실패${NC}"
    exit 1
}

start_backend() {
    echo -e "${YELLOW}[백엔드] 의존성 확인...${NC}"
    cd "$PROJECT_ROOT/backend"
    pip install -q -r requirements.txt 2>/dev/null

    echo -e "${YELLOW}[백엔드] DB 마이그레이션...${NC}"
    alembic upgrade head 2>/dev/null || echo -e "${YELLOW}  (마이그레이션 스킵)${NC}"

    echo -e "${GREEN}[백엔드] 시작 → http://localhost:8000${NC}"
    ENV=development \
    DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/govfinder \
    SECRET_KEY=dev-secret-key-for-local-development-only \
    CORS_ORIGINS=http://localhost:3000 \
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
    BACKEND_PID=$!
    cd "$PROJECT_ROOT"
}

start_frontend() {
    echo -e "${YELLOW}[프론트] 의존성 확인...${NC}"
    cd "$PROJECT_ROOT/frontend"
    if [ ! -d node_modules ]; then
        npm install
    fi

    echo -e "${GREEN}[프론트] 시작 → http://localhost:3000${NC}"
    NEXT_PUBLIC_API_URL=http://localhost:8000 \
    NEXTAUTH_URL=http://localhost:3000 \
    NEXTAUTH_SECRET=dev-nextauth-secret-for-local-only-32chars \
    npm run dev &
    FRONTEND_PID=$!
    cd "$PROJECT_ROOT"
}

stop_db() {
    if docker ps --format '{{.Names}}' | grep -q "^${DB_CONTAINER}$"; then
        docker stop "$DB_CONTAINER" > /dev/null
        echo -e "${GREEN}DB 종료됨${NC}"
    else
        echo "DB 컨테이너가 실행중이 아닙니다."
    fi
}

# ─── Main ───────────────────────────────────────────────

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  SearchPro 로컬 개발 서버${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

case "${1:-all}" in
    db)
        start_db
        ;;
    back)
        start_backend
        wait
        ;;
    front)
        start_frontend
        wait
        ;;
    stop)
        stop_db
        ;;
    all)
        start_db
        echo ""
        start_backend
        echo ""
        start_frontend

        echo ""
        echo -e "${GREEN}========================================${NC}"
        echo -e "${GREEN}  전체 서버 실행 완료!${NC}"
        echo -e "${GREEN}========================================${NC}"
        echo -e "  프론트엔드: ${GREEN}http://localhost:3000${NC}"
        echo -e "  백엔드 API: ${GREEN}http://localhost:8000${NC}"
        echo -e "  API 문서:   ${GREEN}http://localhost:8000/docs${NC}"
        echo ""
        echo -e "  종료: ${YELLOW}Ctrl+C${NC}"
        echo -e "  DB 종료: ${YELLOW}./scripts/dev.sh stop${NC}"
        echo ""

        trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo '서버 종료됨 (DB는 계속 실행중)'; exit 0" INT TERM
        wait
        ;;
    *)
        echo "사용법: ./scripts/dev.sh [all|db|back|front|stop]"
        ;;
esac
