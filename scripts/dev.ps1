# SearchPro 로컬 개발 서버 (PowerShell)
#
# 사용법:
#   .\scripts\dev.ps1          # 전체 실행
#   .\scripts\dev.ps1 db       # DB만
#   .\scripts\dev.ps1 back     # 백엔드만
#   .\scripts\dev.ps1 front    # 프론트엔드만
#   .\scripts\dev.ps1 stop     # 전체 종료

param([string]$Command = "all")

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
$DbContainer = "searchpro-pg"

function Start-Database {
    Write-Host "`n[DB] PostgreSQL 시작..." -ForegroundColor Yellow

    $running = docker ps --format "{{.Names}}" | Select-String -Pattern "^$DbContainer$"
    if ($running) {
        Write-Host "  DB 이미 실행중" -ForegroundColor Green
        return
    }

    $exists = docker ps -a --format "{{.Names}}" | Select-String -Pattern "^$DbContainer$"
    if ($exists) {
        Write-Host "  DB 컨테이너 재시작..." -ForegroundColor Yellow
        docker start $DbContainer | Out-Null
    } else {
        Write-Host "  DB 컨테이너 생성..." -ForegroundColor Yellow
        docker run -d `
            --name $DbContainer `
            -e POSTGRES_DB=govfinder `
            -e POSTGRES_USER=postgres `
            -e POSTGRES_PASSWORD=postgres `
            -p 5432:5432 `
            -v "${ProjectRoot}\docker\pgdata:/var/lib/postgresql/data" `
            postgres:16 | Out-Null
    }

    Write-Host "  DB 준비 대기중..." -ForegroundColor Yellow
    for ($i = 0; $i -lt 30; $i++) {
        $ready = docker exec $DbContainer pg_isready -U postgres 2>&1
        if ($LASTEXITCODE -eq 0) {
            docker exec $DbContainer psql -U postgres -d govfinder -c "CREATE EXTENSION IF NOT EXISTS pg_trgm;" 2>&1 | Out-Null
            Write-Host "  DB 준비 완료 (localhost:5432)" -ForegroundColor Green
            return
        }
        Start-Sleep -Seconds 1
    }
    Write-Host "  DB 시작 실패" -ForegroundColor Red
    exit 1
}

function Start-Backend {
    Write-Host "`n[백엔드] 시작 준비..." -ForegroundColor Yellow
    Push-Location "$ProjectRoot\backend"

    pip install -q -r requirements.txt 2>$null

    Write-Host "[백엔드] DB 마이그레이션..." -ForegroundColor Yellow
    $env:DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/govfinder"
    $env:SECRET_KEY = "dev-secret-key-for-local-development-only"
    $env:ENV = "development"
    $env:CORS_ORIGINS = "http://localhost:3000"
    alembic upgrade head 2>$null

    Write-Host "[백엔드] 시작 -> http://localhost:8000" -ForegroundColor Green

    if ($Command -eq "back") {
        uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    } else {
        Start-Process -FilePath "cmd.exe" -ArgumentList "/k", "title SearchPro-Backend && cd /d $ProjectRoot\backend && set DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/govfinder && set SECRET_KEY=dev-secret-key-for-local-development-only && set ENV=development && set CORS_ORIGINS=http://localhost:3000 && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
    }
    Pop-Location
}

function Start-Frontend {
    Write-Host "`n[프론트] 시작 준비..." -ForegroundColor Yellow
    Push-Location "$ProjectRoot\frontend"

    if (-not (Test-Path "node_modules")) {
        Write-Host "[프론트] npm install..." -ForegroundColor Yellow
        npm install
    }

    Write-Host "[프론트] 시작 -> http://localhost:3000" -ForegroundColor Green

    if ($Command -eq "front") {
        $env:NEXT_PUBLIC_API_URL = "http://localhost:8000"
        $env:NEXTAUTH_URL = "http://localhost:3000"
        $env:NEXTAUTH_SECRET = "dev-nextauth-secret-for-local-only-32chars"
        npm run dev
    } else {
        Start-Process -FilePath "cmd.exe" -ArgumentList "/k", "title SearchPro-Frontend && cd /d $ProjectRoot\frontend && set NEXT_PUBLIC_API_URL=http://localhost:8000 && set NEXTAUTH_URL=http://localhost:3000 && set NEXTAUTH_SECRET=dev-nextauth-secret-for-local-only-32chars && npm run dev"
    }
    Pop-Location
}

function Stop-All {
    Write-Host "`n서버 종료중..." -ForegroundColor Yellow

    # DB
    $running = docker ps --format "{{.Names}}" | Select-String -Pattern "^$DbContainer$"
    if ($running) {
        docker stop $DbContainer | Out-Null
        Write-Host "  DB 종료됨" -ForegroundColor Green
    }

    # Backend/Frontend 창 종료
    Get-Process -Name "uvicorn" -ErrorAction SilentlyContinue | Stop-Process -Force
    taskkill /FI "WINDOWTITLE eq SearchPro-Backend" /F 2>$null | Out-Null
    taskkill /FI "WINDOWTITLE eq SearchPro-Frontend" /F 2>$null | Out-Null
    Write-Host "  서버 프로세스 종료됨" -ForegroundColor Green
}

# ─── Main ───────────────────────────────────────────

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  SearchPro 로컬 개발 서버" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

switch ($Command) {
    "db"    { Start-Database }
    "back"  { Start-Database; Start-Backend }
    "front" { Start-Frontend }
    "stop"  { Stop-All }
    "all"   {
        Start-Database
        Start-Backend
        Start-Frontend

        Write-Host "`n========================================" -ForegroundColor Green
        Write-Host "  전체 서버 실행 완료!" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "  프론트엔드: http://localhost:3000" -ForegroundColor White
        Write-Host "  백엔드 API: http://localhost:8000" -ForegroundColor White
        Write-Host "  API 문서:   http://localhost:8000/docs" -ForegroundColor White
        Write-Host ""
        Write-Host "  종료: .\scripts\dev.ps1 stop" -ForegroundColor Yellow
        Write-Host ""
    }
    default {
        Write-Host "사용법: .\scripts\dev.ps1 [all|db|back|front|stop]"
    }
}
