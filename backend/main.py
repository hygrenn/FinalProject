from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.sessions import SessionMiddleware

from api.middleware.rate_limit import limiter
from api.routes import ai as ai_router
from api.routes import alerts as alerts_router
from api.routes import auth as auth_router
from api.routes import portfolio as portfolio_router
from api.routes import realtime as realtime_router
from api.routes import risk as risk_router
from api.routes import stocks as stocks_router
from api.routes import trades as trades_router
from core.config import settings
from core.redis_client import close_redis
from services.websocket_service import kis_pool


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = AsyncIOScheduler()
    from tasks.ai_tasks import refresh_ai_signals
    from tasks.email_tasks import check_daily_loss, check_price_alerts

    scheduler.add_job(
        refresh_ai_signals.delay, "cron",
        hour=15, minute=35, day_of_week="mon-fri", timezone="Asia/Seoul",
    )
    scheduler.add_job(check_price_alerts.delay, "interval", minutes=5)
    scheduler.add_job(check_daily_loss.delay, "interval", minutes=10)
    scheduler.start()
    yield
    scheduler.shutdown()
    await kis_pool.stop()
    await close_redis()


app = FastAPI(title="StockSenseAI API", lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router, prefix="/auth", tags=["auth"])
app.include_router(stocks_router.router, prefix="/stocks", tags=["stocks"])
app.include_router(realtime_router.router, tags=["realtime"])
app.include_router(ai_router.router, prefix="/ai", tags=["ai"])
app.include_router(trades_router.router, prefix="/trades", tags=["trades"])
app.include_router(portfolio_router.router, prefix="/portfolio", tags=["portfolio"])
app.include_router(risk_router.router, prefix="/risk", tags=["risk"])
app.include_router(alerts_router.router, prefix="/alerts", tags=["alerts"])


@app.get("/health")
async def health():
    return {"status": "ok"}
