"""AI 서비스 — 공고문 구조화 요약 생성

OpenAI API (gpt-4o-mini) 또는 Anthropic Claude Haiku를 사용하여
공고문을 예비창업자 관점에서 구조화 요약합니다.
"""

import logging
from datetime import datetime

import httpx
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import async_session
from app.models.program import Program

logger = logging.getLogger(__name__)

SUMMARY_PROMPT = """아래 정부 지원사업 공고를 예비창업자가 빠르게 이해할 수 있도록 다음 항목으로 정리해주세요:

✅ 한줄 요약
💰 지원내용 (금액, 혜택)
🎯 신청자격 (핵심 조건만)
📅 일정 (접수기간, 선정시기)
📋 필요서류 (주요 항목)
⚠️ 주의사항

간결하고 명확하게, 한국어로 작성해주세요. 정보가 없는 항목은 "원문 확인 필요"로 표기하세요.

---
제목: {title}
기관: {organization}
카테고리: {category}
지역: {region}
지원대상: {target_type}
지원금액: {support_amount}
접수기간: {period}
상세내용:
{description}

자격요건:
{eligibility}
"""

# 하루 최대 요약 생성 수 (비용 관리)
DAILY_LIMIT = 100
MAX_RETRIES = 3


async def _get_today_summary_count() -> int:
    """오늘 생성된 요약 수를 반환한다."""
    async with async_session() as session:
        result = await session.execute(
            select(func.count())
            .select_from(Program)
            .where(
                Program.summary.is_not(None),
                Program.updated_at >= datetime.now().replace(hour=0, minute=0, second=0),
            )
        )
        return result.scalar() or 0


def _build_prompt(program: Program) -> str:
    period = ""
    if program.application_start or program.application_end:
        start = program.application_start.strftime("%Y.%m.%d") if program.application_start else "미정"
        end = program.application_end.strftime("%Y.%m.%d") if program.application_end else "미정"
        period = f"{start} ~ {end}"

    return SUMMARY_PROMPT.format(
        title=program.title or "",
        organization=program.organization or "미상",
        category=program.category or "미분류",
        region=program.region or "미상",
        target_type=program.target_type or "미상",
        support_amount=program.support_amount or "미상",
        period=period or "미상",
        description=(program.description or "내용 없음")[:2000],
        eligibility=(program.eligibility or "내용 없음")[:1000],
    )


async def _call_openai(prompt: str) -> str | None:
    """OpenAI GPT-4o-mini API 호출."""
    if not settings.OPENAI_API_KEY:
        return None

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": "당신은 정부 지원사업 전문 분석가입니다."},
                        {"role": "user", "content": prompt},
                    ],
                    "max_tokens": 1000,
                    "temperature": 0.3,
                },
                timeout=30,
            )
            if resp.status_code == 200:
                data = resp.json()
                return data["choices"][0]["message"]["content"]
            logger.warning("OpenAI API error: %s %s", resp.status_code, resp.text[:200])
            return None
    except Exception as e:
        logger.exception("OpenAI API call failed: %s", e)
        return None


async def _call_anthropic(prompt: str) -> str | None:
    """Anthropic Claude Haiku API 호출 (폴백)."""
    anthropic_key = getattr(settings, "ANTHROPIC_API_KEY", "")
    if not anthropic_key:
        return None

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": anthropic_key,
                    "anthropic-version": "2023-06-01",
                },
                json={
                    "model": "claude-haiku-4-5-20251001",
                    "max_tokens": 1000,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=30,
            )
            if resp.status_code == 200:
                data = resp.json()
                return data["content"][0]["text"]
            logger.warning("Anthropic API error: %s %s", resp.status_code, resp.text[:200])
            return None
    except Exception as e:
        logger.exception("Anthropic API call failed: %s", e)
        return None


async def summarize_program(program: Program) -> str | None:
    """공고문 AI 요약을 생성한다. 이미 요약이 있으면 캐시 반환."""
    if program.summary:
        return program.summary

    prompt = _build_prompt(program)

    # OpenAI 우선, 실패 시 Anthropic 폴백
    for attempt in range(MAX_RETRIES):
        summary = await _call_openai(prompt)
        if summary:
            break
        summary = await _call_anthropic(prompt)
        if summary:
            break

    if not summary:
        logger.warning("All AI providers failed for program %s", program.id)
        return None

    # DB에 저장
    async with async_session() as session:
        await session.execute(
            Program.__table__.update()
            .where(Program.id == program.id)
            .values(summary=summary, updated_at=datetime.now())
        )
        await session.commit()

    return summary


async def batch_summarize_new_programs(limit: int | None = None) -> int:
    """요약이 없는 새 공고에 대해 일괄 요약을 생성한다.
    하루 DAILY_LIMIT 건 제한. 생성 건수를 반환한다.
    """
    today_count = await _get_today_summary_count()
    remaining = DAILY_LIMIT - today_count
    if remaining <= 0:
        logger.info("Daily summary limit reached (%d/%d)", today_count, DAILY_LIMIT)
        return 0

    batch_limit = min(remaining, limit or remaining)

    async with async_session() as session:
        result = await session.execute(
            select(Program)
            .where(Program.summary.is_(None))
            .where(Program.description.is_not(None))
            .order_by(Program.created_at.desc())
            .limit(batch_limit)
        )
        programs = list(result.scalars().all())

    count = 0
    for prog in programs:
        summary = await summarize_program(prog)
        if summary:
            count += 1

    logger.info("Batch summarize: %d/%d programs", count, len(programs))
    return count
