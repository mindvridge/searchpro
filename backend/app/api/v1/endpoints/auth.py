"""사용자 인증 엔드포인트 — 회원가입, 로그인, 카카오 OAuth, 프로필"""

from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.auth import (
    clear_auth_cookies,
    get_current_user,
    hash_password,
    set_auth_cookies,
    verify_password,
)
from app.database import get_db
from app.models.user import ProviderType, User
from app.schemas.user import UserResponse, UserUpdate

router = APIRouter(prefix="/auth", tags=["auth"])


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str | None = None


class LoginRequest(BaseModel):
    email: str
    password: str


class KakaoCallbackRequest(BaseModel):
    access_token: str


class ProfileUpdateRequest(BaseModel):
    name: str | None = None
    profile: dict | None = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


# ---------------------------------------------------------------------------
# POST /auth/register
# ---------------------------------------------------------------------------


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(
    body: RegisterRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
        name=body.name,
        provider=ProviderType.EMAIL,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    tokens = set_auth_cookies(response, str(user.id))
    return TokenResponse(**tokens, user=UserResponse.model_validate(user))


# ---------------------------------------------------------------------------
# POST /auth/login
# ---------------------------------------------------------------------------


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if not user or not user.password_hash:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    tokens = set_auth_cookies(response, str(user.id))
    return TokenResponse(**tokens, user=UserResponse.model_validate(user))


# ---------------------------------------------------------------------------
# POST /auth/kakao
# ---------------------------------------------------------------------------


@router.post("/kakao", response_model=TokenResponse)
async def kakao_callback(
    body: KakaoCallbackRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """카카오 OAuth access_token으로 사용자 정보를 가져와 로그인/가입 처리."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://kapi.kakao.com/v2/user/me",
            headers={"Authorization": f"Bearer {body.access_token}"},
            timeout=10,
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid Kakao access token")
        kakao_user = resp.json()

    kakao_id = str(kakao_user["id"])
    kakao_email = (
        kakao_user.get("kakao_account", {}).get("email")
        or f"kakao_{kakao_id}@kakao.local"
    )
    kakao_name = kakao_user.get("kakao_account", {}).get("profile", {}).get("nickname")

    # 기존 카카오 사용자 찾기
    result = await db.execute(
        select(User).where(User.provider == ProviderType.KAKAO, User.provider_id == kakao_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        # 같은 이메일 사용자가 있는지 확인
        result = await db.execute(select(User).where(User.email == kakao_email))
        user = result.scalar_one_or_none()
        if user:
            # 기존 이메일 계정에 카카오 연동
            user.provider = ProviderType.KAKAO
            user.provider_id = kakao_id
            if kakao_name and not user.name:
                user.name = kakao_name
        else:
            # 신규 가입
            user = User(
                email=kakao_email,
                name=kakao_name,
                provider=ProviderType.KAKAO,
                provider_id=kakao_id,
            )
            db.add(user)

        await db.commit()
        await db.refresh(user)

    tokens = set_auth_cookies(response, str(user.id))
    return TokenResponse(**tokens, user=UserResponse.model_validate(user))


# ---------------------------------------------------------------------------
# POST /auth/logout
# ---------------------------------------------------------------------------


@router.post("/logout")
async def logout(response: Response):
    clear_auth_cookies(response)
    return {"message": "Logged out"}


# ---------------------------------------------------------------------------
# GET /auth/me
# ---------------------------------------------------------------------------


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    return UserResponse.model_validate(user)


# ---------------------------------------------------------------------------
# PUT /auth/profile
# ---------------------------------------------------------------------------


@router.put("/profile", response_model=UserResponse)
async def update_profile(
    body: ProfileUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.name is not None:
        user.name = body.name
    if body.profile is not None:
        user.profile = body.profile

    db.add(user)
    await db.commit()
    await db.refresh(user)
    return UserResponse.model_validate(user)
