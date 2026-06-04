import asyncio

from tasks import celery_app


def _get_notification_email(user_id: str) -> str | None:
    """notification_email 설정 or user.email fallback."""
    import uuid
    from core.database import AsyncSessionLocal
    from models.risk import AlertSettings
    from models.user import User
    from sqlalchemy import select

    async def _fetch():
        async with AsyncSessionLocal() as db:
            uid = uuid.UUID(user_id)
            result = await db.execute(select(AlertSettings).where(AlertSettings.user_id == uid))
            alert = result.scalar_one_or_none()
            if alert and alert.notification_email:
                return alert.notification_email
            result2 = await db.execute(select(User).where(User.id == uid))
            user = result2.scalar_one_or_none()
            return user.email if user else None

    return asyncio.run(_fetch())


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_fill_notification(self, user_id: str, trade_id: str) -> None:
    """체결 완료 이메일."""
    import asyncio
    import uuid
    from core.database import AsyncSessionLocal
    from models.trade import Trade
    from sqlalchemy import select

    async def _fetch_trade():
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Trade).where(Trade.id == uuid.UUID(trade_id)))
            return result.scalar_one_or_none()

    trade = asyncio.run(_fetch_trade())
    if not trade:
        return

    to_email = _get_notification_email(user_id)
    if not to_email:
        return

    order_type_kr = "매수" if trade.order_type == "BUY" else "매도"
    subject = f"[StockSenseAI] {trade.stock_code} {order_type_kr} 체결 완료"
    body = (
        f"<p>{trade.stock_code} {trade.stock_name or ''} {order_type_kr} 체결되었습니다.</p>"
        f"<p>체결가: {trade.executed_price:,}원 | 수량: {trade.quantity}주</p>"
    )

    try:
        from core.config import settings
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail

        if not settings.SENDGRID_API_KEY:
            return
        msg = Mail(from_email=settings.FROM_EMAIL, to_emails=to_email,
                   subject=subject, html_content=body)
        client = SendGridAPIClient(settings.SENDGRID_API_KEY)
        asyncio.run(asyncio.to_thread(client.send, msg))
    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_risk_alert(self, user_id: str, reason: str) -> None:
    """리스크 한도 초과 경고 이메일."""
    to_email = _get_notification_email(user_id)
    if not to_email:
        return
    try:
        import asyncio
        from core.config import settings
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail

        if not settings.SENDGRID_API_KEY:
            return
        msg = Mail(
            from_email=settings.FROM_EMAIL,
            to_emails=to_email,
            subject="[StockSenseAI] 리스크 한도 초과 경고",
            html_content=f"<p>리스크 한도 초과: {reason}</p>",
        )
        client = SendGridAPIClient(settings.SENDGRID_API_KEY)
        asyncio.run(asyncio.to_thread(client.send, msg))
    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task
def check_price_alerts() -> None:
    """관심종목 목표가 도달 시 이메일 — APScheduler 5분 간격 (Phase 4-D에서 구현)."""
    pass


@celery_app.task
def check_daily_loss() -> None:
    """일일 손실 한도 체크 — APScheduler 10분 간격 (Phase 4-D에서 구현)."""
    pass
