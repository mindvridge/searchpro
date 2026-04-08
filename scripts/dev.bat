@echo off
chcp 65001 >nul
title SearchPro 로컬 개발 서버

:: ========================================
::  SearchPro 로컬 개발 서버 (Windows)
::
::  사용법:
::    dev.bat          전체 실행 (DB + 백엔드 + 프론트엔드)
::    dev.bat db       DB만 실행
::    dev.bat back     백엔드만 실행
::    dev.bat front    프론트엔드만 실행
::    dev.bat stop     DB 컨테이너 종료
:: ========================================

set DB_CONTAINER=searchpro-pg
set PROJECT_ROOT=%~dp0..
pushd %PROJECT_ROOT%

if "%1"=="" goto all
if "%1"=="all" goto all
if "%1"=="db" goto db
if "%1"=="back" goto back
if "%1"=="front" goto front
if "%1"=="stop" goto stop
echo 사용법: dev.bat [all^|db^|back^|front^|stop]
goto end

:: ─── DB ────────────────────────────────────────────

:db
echo.
echo [DB] PostgreSQL 시작...

docker ps --format "{{.Names}}" | findstr /C:"%DB_CONTAINER%" >nul 2>&1
if %ERRORLEVEL%==0 (
    echo   DB 이미 실행중
    goto db_ready
)

docker ps -a --format "{{.Names}}" | findstr /C:"%DB_CONTAINER%" >nul 2>&1
if %ERRORLEVEL%==0 (
    echo   DB 컨테이너 재시작...
    docker start %DB_CONTAINER% >nul
) else (
    echo   DB 컨테이너 생성...
    docker run -d ^
        --name %DB_CONTAINER% ^
        -e POSTGRES_DB=govfinder ^
        -e POSTGRES_USER=postgres ^
        -e POSTGRES_PASSWORD=postgres ^
        -p 5432:5432 ^
        -v "%PROJECT_ROOT%\docker\pgdata:/var/lib/postgresql/data" ^
        postgres:16 >nul
)

echo   DB 준비 대기중...
set /a count=0
:db_wait
if %count% geq 30 (
    echo   DB 시작 실패
    goto end
)
timeout /t 1 /nobreak >nul
docker exec %DB_CONTAINER% pg_isready -U postgres >nul 2>&1
if %ERRORLEVEL% neq 0 (
    set /a count+=1
    goto db_wait
)

:: pg_trgm 확장 활성화
docker exec %DB_CONTAINER% psql -U postgres -d govfinder -c "CREATE EXTENSION IF NOT EXISTS pg_trgm;" >nul 2>&1

:db_ready
echo   DB 준비 완료 (localhost:5432)
if "%1"=="db" goto end
goto :eof

:: ─── Backend ───────────────────────────────────────

:back
echo.
echo [백엔드] 의존성 설치...
pushd backend
pip install -q -r requirements.txt 2>nul

echo [백엔드] DB 마이그레이션...
set DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/govfinder
set SECRET_KEY=dev-secret-key-for-local-development-only
set ENV=development
set CORS_ORIGINS=http://localhost:3000
alembic upgrade head 2>nul

echo [백엔드] 시작 → http://localhost:8000
if "%1"=="back" (
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
) else (
    start "SearchPro-Backend" cmd /c "cd /d %PROJECT_ROOT%\backend && set DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/govfinder && set SECRET_KEY=dev-secret-key-for-local-development-only && set ENV=development && set CORS_ORIGINS=http://localhost:3000 && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
)
popd
if "%1"=="back" goto end
goto :eof

:: ─── Frontend ──────────────────────────────────────

:front
echo.
echo [프론트] 의존성 확인...
pushd frontend
if not exist node_modules (
    echo [프론트] npm install 실행중...
    call npm install
)

echo [프론트] 시작 → http://localhost:3000
if "%1"=="front" (
    set NEXT_PUBLIC_API_URL=http://localhost:8000
    set NEXTAUTH_URL=http://localhost:3000
    set NEXTAUTH_SECRET=dev-nextauth-secret-for-local-only-32chars
    call npm run dev
) else (
    start "SearchPro-Frontend" cmd /c "cd /d %PROJECT_ROOT%\frontend && set NEXT_PUBLIC_API_URL=http://localhost:8000 && set NEXTAUTH_URL=http://localhost:3000 && set NEXTAUTH_SECRET=dev-nextauth-secret-for-local-only-32chars && npm run dev"
)
popd
if "%1"=="front" goto end
goto :eof

:: ─── Stop ──────────────────────────────────────────

:stop
echo.
docker ps --format "{{.Names}}" | findstr /C:"%DB_CONTAINER%" >nul 2>&1
if %ERRORLEVEL%==0 (
    docker stop %DB_CONTAINER% >nul
    echo DB 종료됨
) else (
    echo DB 컨테이너가 실행중이 아닙니다.
)

:: 백엔드/프론트엔드 프로세스 종료
taskkill /FI "WINDOWTITLE eq SearchPro-Backend" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq SearchPro-Frontend" /F >nul 2>&1
echo 서버 프로세스 종료됨
goto end

:: ─── All ───────────────────────────────────────────

:all
echo ========================================
echo   SearchPro 로컬 개발 서버 (Windows)
echo ========================================
echo.

call :db
call :back
call :front

echo.
echo ========================================
echo   전체 서버 실행 완료!
echo ========================================
echo   프론트엔드: http://localhost:3000
echo   백엔드 API: http://localhost:8000
echo   API 문서:   http://localhost:8000/docs
echo.
echo   종료: dev.bat stop
echo.
echo   백엔드/프론트엔드가 새 창에서 실행중입니다.
echo   이 창은 닫아도 됩니다.
echo.
goto end

:end
popd 2>nul
