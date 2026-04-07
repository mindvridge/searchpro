#!/bin/bash
# SearchPro 로컬 개발 서버 실행
#
# 사용법:
#   ./scripts/dev.sh          # Docker로 전체 실행
#   ./scripts/dev.sh --no-docker  # Docker 없이 (Python + Node 직접 실행)

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  SearchPro 로컬 개발 서버${NC}"
echo -e "${GREEN}========================================${NC}"

if [ "$1" = "--no-docker" ]; then
    echo -e "${YELLOW}Docker 없이 직접 실행 모드${NC}"
    echo ""

    # .env 파일 확인
    if [ ! -f .env ]; then
        echo -e "${YELLOW}.env 파일 생성 중...${NC}"
        cp .env.example .env
        # 개발용 기본값 설정
        sed -i 's/your-secret-key-min-32-chars-long-here/dev-secret-key-for-local-development-only/' .env
        sed -i 's/your-nextauth-secret-min-32-chars/dev-nextauth-secret-for-local-only-32chars/' .env
    fi

    # PostgreSQL 확인
    if ! pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
        echo -e "${RED}PostgreSQL이 실행중이지 않습니다.${NC}"
        echo "  다음 중 하나를 실행하세요:"
        echo "    docker run -d --name searchpro-pg -e POSTGRES_DB=govfinder -e POSTGRES_PASSWORD=postgres -p 5432:5432 postgres:16"
        echo "    또는 로컬 PostgreSQL에 govfinder DB를 생성하세요."
        exit 1
    fi

    # 백엔드 의존성 설치 + 마이그레이션
    echo -e "${YELLOW}[1/4] 백엔드 의존성 설치...${NC}"
    cd backend
    pip install -q -r requirements.txt 2>/dev/null

    echo -e "${YELLOW}[2/4] DB 마이그레이션...${NC}"
    alembic upgrade head 2>/dev/null || echo -e "${YELLOW}  (마이그레이션 스킵 — DB 연결 확인 필요)${NC}"

    echo -e "${YELLOW}[3/4] 백엔드 시작 (port 8000)...${NC}"
    ENV=development uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
    BACKEND_PID=$!
    cd ..

    # 프론트엔드
    echo -e "${YELLOW}[4/4] 프론트엔드 시작 (port 3000)...${NC}"
    cd frontend
    npm install --silent 2>/dev/null
    NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev &
    FRONTEND_PID=$!
    cd ..

    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  서버 실행 완료!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo -e "  프론트엔드: ${GREEN}http://localhost:3000${NC}"
    echo -e "  백엔드 API: ${GREEN}http://localhost:8000${NC}"
    echo -e "  API 문서:   ${GREEN}http://localhost:8000/docs${NC}"
    echo ""
    echo -e "  종료: ${YELLOW}Ctrl+C${NC}"
    echo ""

    # Ctrl+C로 양쪽 다 종료
    trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT TERM
    wait

else
    echo -e "${YELLOW}Docker Compose로 실행${NC}"
    echo ""

    # Docker 확인
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Docker가 설치되어 있지 않습니다.${NC}"
        exit 1
    fi

    echo -e "${YELLOW}[1/2] 빌드 및 시작...${NC}"
    docker compose up --build -d

    echo ""
    echo -e "${YELLOW}[2/2] 서비스 상태 확인 중...${NC}"
    sleep 3

    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  서버 실행 완료!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo -e "  프론트엔드: ${GREEN}http://localhost:3000${NC}"
    echo -e "  백엔드 API: ${GREEN}http://localhost:8000${NC}"
    echo -e "  API 문서:   ${GREEN}http://localhost:8000/docs${NC}"
    echo -e "  PostgreSQL: ${GREEN}localhost:5432${NC} (DB: govfinder)"
    echo ""
    echo -e "  로그 보기: ${YELLOW}docker compose logs -f${NC}"
    echo -e "  종료:      ${YELLOW}docker compose down${NC}"
    echo ""
fi
