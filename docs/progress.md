# StockSenseAI — Phase별 진행 현황

**최종 업데이트:** 2026-06-02
**레포:** https://github.com/hygrenn/FinalProject | **브랜치:** `hwang` (백엔드), `seogu-Jeong` (프론트)

---

## 전체 Phase 구성

| Phase | 주제 | 담당 | 상태 |
|---|---|---|---|
| Phase 1 | 인증 + 기본 시세 API + 인프라 | hygrenn | ✅ 완료 |
| Phase 2 | 실시간 시세 + WebSocket + 차트 고도화 | hygrenn | 🔲 미시작 |
| Phase 3 | AI 예측 + 시그널 + 패턴 인식 | hygrenn | 🔲 미시작 |
| Phase 4 | 거래 + 포트폴리오 + 시뮬레이터 + 리스크 | hygrenn | 🔲 미시작 |
| 프론트 전체 | 레이아웃 → 차트 → AI UI → 거래 UI | seogu-Jeong | 🔲 진행 중 |

---

## Phase 1 — 인증 + 기본 시세 API + 인프라 ✅

**완료일:** 2026-06-02 | **테스트:** 30/30 passing | **커밋:** `ec11bf5`

### 인프라

| 컴포넌트 | 파일 | 상태 |
|---|---|---|
| Docker Compose (postgres 15, redis 7, backend, celery) | `docker-compose.yml` | ✅ |
| PostgreSQL healthcheck + celery service_healthy 의존성 | `docker-compose.yml` | ✅ |
| Alembic 비동기 마이그레이션 (`async_engine_from_config`) | `db/migrations/` | ✅ |
| Celery stub (`tasks.py`) | `backend/tasks.py` | ✅ |
| `.env.example` (전체 환경변수 문서화) | `.env.example` | ✅ |

### 코어 레이어

| 컴포넌트 | 파일 | 비고 |
|---|---|---|
| pydantic-settings 설정 (`DATABASE_URL` 자동 조합 validator 포함) | `backend/core/config.py` | ✅ |
| async SQLAlchemy 엔진 + `get_db` | `backend/core/database.py` | ✅ |
| Redis 연결 풀 (lazy singleton) | `backend/core/redis_client.py` | ✅ |
| JWT (HS256, 30분) + Refresh Token (bcrypt hash, 7일) | `backend/core/security.py` | ✅ |
| AES-256-GCM 암호화/복호화 (모듈 로드 시 키 사전계산) | `backend/core/security.py` | ✅ |
| 이메일 인증 토큰 (type claim 포함, 30분) | `backend/core/security.py` | ✅ |

### DB 모델 & 마이그레이션

| 컴포넌트 | 파일 | 비고 |
|---|---|---|
| `users` 테이블 (UUID PK, CheckConstraint on mode, nullable=False 명시) | `backend/models/user.py` | ✅ |
| `refresh_tokens` 테이블 (selector 컬럼 + 복합 인덱스) | `backend/models/user.py` | ✅ |
| Initial schema 마이그레이션 | `db/migrations/versions/*_initial_schema.py` | ✅ |
| Selector 컬럼 추가 마이그레이션 | `db/migrations/versions/*_add_refresh_token_selector.py` | ✅ |

### 인증 API (`/auth`)

| 엔드포인트 | 설명 | 상태 |
|---|---|---|
| `POST /auth/register` | 이메일 가입, 중복 체크(409), 인증 메일 발송 | ✅ |
| `POST /auth/verify-email` | JWT 토큰으로 `is_verified=True` | ✅ |
| `POST /auth/login` | bcrypt 검증, Refresh Token Rotation, HttpOnly Cookie | ✅ |
| `POST /auth/refresh` | selector 인덱스 조회 → bcrypt 검증 → 토큰 교체 | ✅ |
| `POST /auth/logout` | Refresh Token revoked=True, 쿠키 삭제 | ✅ |
| `GET /auth/me` | JWT 인증 후 내 정보 반환 | ✅ |
| `PUT /auth/api-key` | KIS 키 AES-256-GCM 암호화 저장, 개발환경 연결 테스트 스킵 | ✅ |
| `GET /auth/google` | Google OAuth 동의 화면 리다이렉트 | ✅ |
| `GET /auth/google/callback` | upsert by email, JWT → 프론트 리다이렉트 | ✅ |

**보안 처리 포인트:**
- Refresh Token: `selector(16자) + bcrypt(verifier)` 구조 → O(1) DB 조회
- Cookie: `secure=True` (APP_ENV != development), `httponly=True`, `samesite=lax`
- Rate Limit: 로그인 5회/분, 일반 API 100회/분 (slowapi default_limits)
- KIS 키: `Literal["paper", "real"]` Pydantic 검증 + AES-256-GCM 암호화

### 시세 API (`/stocks`)

| 엔드포인트 | 설명 | 상태 |
|---|---|---|
| `GET /stocks` | 코스피/코스닥 종목 목록 (페이지네이션) | ✅ |
| `GET /stocks/search` | 종목명/코드 검색 (최대 20건) | ✅ |
| `GET /stocks/indices` | 코스피/코스닥 지수 | ✅ |
| `GET /stocks/{code}/chart` | OHLCV 차트 (period: 1w~3y, interval: day/week/month) | ✅ |
| `GET /stocks/{code}` | 종목 현재가 | ✅ |

**캐싱 전략:**
- 장중 (평일 09:00~15:30): Redis TTL 30초
- 장외: Redis TTL 24시간 (차트), 3600초 (지수)
- 종목 목록: Redis TTL 24시간

### 미들웨어 & 공통

| 컴포넌트 | 파일 | 상태 |
|---|---|---|
| JWT `get_current_user` (명시적 UUID 파싱 포함) | `backend/api/deps.py` | ✅ |
| slowapi Limiter (default_limits 100/min) | `backend/api/middleware/rate_limit.py` | ✅ |
| CORS + SessionMiddleware + SlowAPIMiddleware | `backend/main.py` | ✅ |
| SendGrid 이메일 서비스 (`asyncio.to_thread` + 오류 무시) | `backend/services/email_service.py` | ✅ |
| KIS 연결 테스트 stub (httpx async) | `backend/services/kis_service.py` | ✅ |
| pykrx OHLCV 수집 + Redis 캐싱 | `backend/services/market_service.py` | ✅ |

### 테스트

| 파일 | 테스트 수 | 커버리지 |
|---|---|---|
| `tests/test_security.py` | 10 | JWT, bcrypt, AES-256-GCM 유닛 |
| `tests/test_auth.py` | 14 | 전체 `/auth` 통합 (register→verify→login→refresh→logout→me→kis) |
| `tests/test_stocks.py` | 6 | 라우터/서비스 mock 기반 통합 (Redis 캐시 hit/miss, 각 stocks 엔드포인트) |
| **합계** | **30** | **30/30 passing** |

> 참고: stocks 테스트는 pykrx/Redis 실제 연동이 아닌 mock 기반 통합 테스트입니다. 별도 Redis/pykrx smoke test는 추후 추가 예정.

---

## Phase 2 — 실시간 시세 + WebSocket 🔲

**목표:** KIS WebSocket 연동으로 실시간 체결/호가 데이터 스트리밍

### 구현 예정 항목

| 컴포넌트 | 설명 |
|---|---|
| `services/websocket_service.py` | KIS WebSocket Pool (41종목 제한 처리, Redis Pub/Sub 브로커) |
| `GET /stocks/{code}/orderbook` | 10단 호가 (실시간 or REST 폴백) |
| `GET /stocks/{code}/trades` | 실시간 체결 최근 20건 |
| `GET /ws/stocks/{code}` | SSE or WebSocket 스트리밍 엔드포인트 |
| KIS WebSocket OAuth (approval_key 발급, 24h 세션 갱신) | `services/websocket_service.py` |
| pykrx 분봉 데이터 지원 (`interval: 1min/5min/15min/1h`) | `services/market_service.py` 확장 |

### 관련 KIS TR ID

| 기능 | TR ID |
|---|---|
| WebSocket 현재가 (실시간 체결) | `H0STCNT0` |
| WebSocket 호가 | `H0STASP0` |
| REST 현재가 | `FHKST01010100` |

---

## Phase 3 — AI 예측 + 시그널 + 패턴 인식 🔲

**목표:** LSTM 모델로 5일 예측, 기술적 지표 기반 종합 시그널, 캔들 패턴 감지

### 구현 예정 항목

| 컴포넌트 | 파일 | 설명 |
|---|---|---|
| LSTM 모델 | `backend/ml/model.py` | 입력(batch,60,13) → 출력(batch,5) 변화율 예측, Attention 포함 |
| 피처 엔지니어링 | `backend/ml/features.py` | pandas-ta: RSI, MACD, BB, MA5/20/60, Stoch (13 피처) |
| 학습 스크립트 | `backend/ml/train.py` | Huber Loss + AdamW + CosineAnnealingLR, Early Stopping |
| 추론 | `backend/ml/predict.py` | Monte Carlo Dropout 50회 → bullish/base/bearish 시나리오 |
| 유사 패턴 매칭 | `backend/ml/pattern_matcher.py` | 히스토리에서 유사 패턴 Top 5 검색 |
| AI 서비스 | `backend/services/ai_service.py` | 기술적 지표 40% + LSTM 60% 가중 합산 → BUY/HOLD/SELL |
| 패턴 서비스 | `backend/services/pattern_service.py` | pandas-ta `cdl_pattern()` (14종 패턴) |
| Celery AI 태스크 | `backend/tasks/ai_tasks.py` | 장 종료 후(15:35) 전 종목 시그널 갱신 |

### AI API 엔드포인트 (`/ai`)

| 엔드포인트 | 설명 |
|---|---|
| `GET /ai/{code}/signal` | 종합 AI 시그널 (BUY/HOLD/SELL + score) |
| `GET /ai/{code}/predict` | LSTM 5일 예측 (bullish/base/bearish) |
| `GET /ai/{code}/indicators` | RSI, MACD, BB, MA 원시값 |
| `GET /ai/{code}/patterns` | 감지된 캔들 패턴 목록 |
| `GET /ai/{code}/similar` | 유사 패턴 히스토리 Top 5 |
| `GET /ai/{code}/multiframe` | 일봉/주봉/월봉 멀티타임프레임 시그널 |
| `GET /ai/top-picks` | AI BUY 시그널 상위 종목 (스크리너) |
| `GET /ai/signals/history/{code}` | 시그널 변경 이력 최근 30일 |

**Rate limit:** AI 엔드포인트 20회/분 (TRD 8.3)

---

## Phase 4 — 거래 + 포트폴리오 + 시뮬레이터 + 리스크 🔲

**목표:** KIS REST API 실거래/모의투자 주문, 포트폴리오 추적, 백테스팅, 리스크 관리

### 구현 예정 항목

| 컴포넌트 | 파일 | 설명 |
|---|---|---|
| KIS 서비스 (완전판) | `backend/services/kis_service.py` | 매수(TTTC0802U)/매도(TTTC0801U)/잔고/체결 등 TR ID 매핑, httpx async |
| 리스크 서비스 | `backend/services/risk_service.py` | 종목별 한도, 일일 손실 한도 체크 |
| 백테스팅 엔진 | `backend/services/backtest_service.py` | MDD/샤프비율/승률 계산 |
| 포트폴리오 모델 | `backend/models/portfolio.py` | `portfolios`, `trades`, `risk_settings`, `watchlists`, `alert_settings`, `backtest_results`, `ai_signals_history` 테이블 |
| Celery 태스크 | `backend/tasks/email_tasks.py`, `report_tasks.py` | 이메일 발송, 주간 리포트 (APScheduler) |
| APScheduler | `backend/main.py` | 가격 알림 5분, 손실 체크 10분, AI 갱신 15:35, 주간 리포트 월 08:00 |

### 거래/포트폴리오 API

| 엔드포인트 | 설명 |
|---|---|
| `POST /trades/order` | 리스크 체크 → KIS API 주문 → 체결 폴링 |
| `GET /trades` | 주문 목록 (status, date 필터) |
| `DELETE /trades/{id}` | 미체결 주문 취소 |
| `GET /portfolio` | 보유 종목 현황 + 수익률 |
| `GET /portfolio/performance` | 일별 평가액 히스토리 |
| `GET /portfolio/metrics` | MDD, 샤프비율, 승률 |
| `GET /portfolio/export` | CSV 다운로드 |
| `POST /backtest/run` | 백테스트 실행 (Celery 비동기) |
| `GET /backtest/{id}` | 백테스트 결과 조회 |
| `GET/PUT /risk/settings` | 리스크 설정 조회/수정 |
| `GET/PUT /alerts/settings` | 알림 설정 조회/수정 |

### 투자 시뮬레이터 API (`/simulate`)

| 엔드포인트 | 설명 |
|---|---|
| `POST /simulate/lumpsum` | 일시불 투자 수익률 계산 |
| `POST /simulate/recurring` | 적립식 투자 수익률 계산 |
| `GET /simulate/data-status` | 캐시 데이터 존재 여부 |
| `GET /simulate/download` | 전체 데이터 다운로드 (SSE 스트리밍) |

---

## 프론트엔드 (seogu-Jeong 담당) 🔲

**브랜치:** `seogu-Jeong` | **스택:** React 18 + TypeScript, Vite, shadcn/ui, Tailwind v4, Zustand, Axios

| 화면 | 설명 | 상태 |
|---|---|---|
| 랜딩 + 로그인/회원가입 | Google OAuth + 이메일 인증 UI | 🔲 |
| 메인 차트 화면 | Lightweight Charts 캔들스틱, AI 예측 오버레이 | 🔲 |
| 기술적 지표 패널 | RSI, MACD, 볼린저밴드 | 🔲 |
| AI 시그널 패널 | BUY/HOLD/SELL 스코어, 유사 패턴 | 🔲 |
| 종목 검색/관심종목 | 검색바, 관심종목 그룹 | 🔲 |
| 거래 패널 | 매수/매도 폼, 주문 현황 | 🔲 |
| 포트폴리오 화면 | 보유 종목, 수익률 차트 (Recharts) | 🔲 |
| 투자 시뮬레이터 | ifibought UX 기반 | 🔲 |
| 설정 화면 | KIS 키 등록, 리스크 설정, 알림 | 🔲 |

**백엔드 연동 전까지 mock 데이터로 개발.**
API Base: `http://localhost:8000` (개발), 환경변수: `VITE_API_BASE`

---

## 알려진 제약 / TODO

| 항목 | 내용 |
|---|---|
| Google OAuth refresh token | OAuth 콜백은 spec에 따라 `#token=xxx` redirect만 발급 (refresh token 미발급) |
| pykrx 1.2.8 KRX 로그인 | 환경변수 `KRX_ID`, `KRX_PW` 미설정 시 경고 출력 (데이터 조회는 정상 동작) |
| Docker 빌드 검증 | 로컬 Docker 미설치로 이미지 빌드 미검증 (요구사항 파일은 완비) |
| Nginx | Phase 1 제외, Phase 4 이후 프로덕션 배포 시 추가 |
