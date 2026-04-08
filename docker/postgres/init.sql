-- 로컬 DB 초기화 스크립트
-- docker-entrypoint-initdb.d에 의해 최초 1회 자동 실행됨

CREATE EXTENSION IF NOT EXISTS pg_trgm;
