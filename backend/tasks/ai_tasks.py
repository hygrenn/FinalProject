import asyncio

from tasks import celery_app


@celery_app.task
def refresh_ai_signals() -> None:
    """장 종료 후(15:35) 학습된 전 종목 AI 시그널 갱신."""
    asyncio.run(_refresh_async())


async def _refresh_async() -> None:
    from core.database import AsyncSessionLocal
    from ml.predict import WEIGHTS_DIR
    from services.ai_service import calculate_signal

    codes = [p.stem for p in WEIGHTS_DIR.glob("*.pth")]
    for code in codes:
        try:
            async with AsyncSessionLocal() as db:
                await calculate_signal(code, db)
        except Exception:
            pass
