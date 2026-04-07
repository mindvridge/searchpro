"""JWT 인증 및 비밀번호 해싱 유틸리티"""

from datetime import datetime, timedelta, timezone
from uuid import UUID

import hashlib
import hmac
import secrets

from fastapi import Depends, HTTPException, Request, Response
from joserfc import jwt as jose_jwt
from joserfc.jwk import OctKey
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.user import User

# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------

def hash_password(password: str) -> str:
    """PBKDF2-SHA256 해싱 (salt 포함)."""
    salt = secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 260000)
    return f"{salt}${h.hex()}"


def verify_password(plain: str, hashed: str) -> bool:
    try:
        salt, hash_hex = hashed.split("$", 1)
        h = hashlib.pbkdf2_hmac("sha256", plain.encode(), salt.encode(), 260000)
        return hmac.compare_digest(h.hex(), hash_hex)
    except (ValueError, AttributeError):
        return False


# ---------------------------------------------------------------------------
# JWT
# ---------------------------------------------------------------------------

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE = timedelta(minutes=30)
REFRESH_TOKEN_EXPIRE = timedelta(days=7)

ACCESS_COOKIE = "access_token"
REFRESH_COOKIE = "refresh_token"


def _get_key() -> OctKey:
    return OctKey.import_key(settings.SECRET_KEY)


def create_access_token(user_id: str) -> str:
    expire = int((datetime.now(timezone.utc) + ACCESS_TOKEN_EXPIRE).timestamp())
    token = jose_jwt.encode(
        {"alg": ALGORITHM},
        {"sub": user_id, "exp": expire, "type": "access"},
        _get_key(),
    )
    return token


def create_refresh_token(user_id: str) -> str:
    expire = int((datetime.now(timezone.utc) + REFRESH_TOKEN_EXPIRE).timestamp())
    token = jose_jwt.encode(
        {"alg": ALGORITHM},
        {"sub": user_id, "exp": expire, "type": "refresh"},
        _get_key(),
    )
    return token


def decode_token(token: str) -> dict:
    try:
        result = jose_jwt.decode(token, _get_key())
        claims = result.claims
        # Check expiration
        exp = claims.get("exp")
        if exp and datetime.now(timezone.utc).timestamp() > exp:
            raise HTTPException(status_code=401, detail="Token expired")
        return claims
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def set_auth_cookies(response: Response, user_id: str) -> dict:
    """Access + Refresh 토큰을 HTTPOnly 쿠키로 설정."""
    access = create_access_token(user_id)
    refresh = create_refresh_token(user_id)

    response.set_cookie(
        ACCESS_COOKIE, access,
        httponly=True, samesite="lax", max_age=int(ACCESS_TOKEN_EXPIRE.total_seconds()),
    )
    response.set_cookie(
        REFRESH_COOKIE, refresh,
        httponly=True, samesite="lax", max_age=int(REFRESH_TOKEN_EXPIRE.total_seconds()),
    )
    return {"access_token": access, "refresh_token": refresh, "token_type": "bearer"}


def clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(ACCESS_COOKIE)
    response.delete_cookie(REFRESH_COOKIE)


# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    """쿠키 또는 Authorization 헤더에서 JWT를 추출하여 사용자를 반환."""
    token = request.cookies.get(ACCESS_COOKIE)
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]

    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    payload = decode_token(token)
    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid token type")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = await db.get(User, UUID(user_id))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


async def get_current_user_optional(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """인증이 선택적인 엔드포인트용. 토큰 없으면 None 반환."""
    try:
        return await get_current_user(request, db)
    except HTTPException:
        return None
