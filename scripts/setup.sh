#!/bin/bash
# 프로젝트 초기 세팅 스크립트

set -e

echo "=== SearchPro 개발 환경 설정 ==="

# .env 파일 생성
if [ ! -f .env ]; then
  cp .env.example .env
  echo "✓ .env 파일 생성 완료"
fi

# Docker 서비스 시작
echo "Docker 서비스 시작..."
docker-compose up -d postgres

# 프론트엔드 의존성 설치
echo "프론트엔드 의존성 설치..."
cd frontend && npm install && cd ..

# 백엔드 의존성 설치
echo "백엔드 의존성 설치..."
cd backend && pip install -r requirements.txt && cd ..

echo "=== 설정 완료 ==="
echo "프론트엔드: cd frontend && npm run dev"
echo "백엔드: docker-compose up"
