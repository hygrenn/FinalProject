# StockSenseAI — AI Agent 협업 가이드

**PRD/TRD 전체 명세:** `docs/superpowers/specs/` 폴더 참고. 작업 전 반드시 읽을 것.

---

## 프로젝트

AI 기반 한국 주식 차트 예측 + 실거래 실행 통합 웹 서비스.
레포: https://github.com/hygrenn/FinalProject

---

## 담당 분리

| 개발자 | 브랜치 | 담당 |
|---|---|---|
| 황윤광 (hygrenn) | `hwang` | 백엔드 + ML + 인프라 |
| 정석우 (seogu-Jeong) | `seogu-Jeong` | 프론트엔드 |

- `frontend/` — seogu-Jeong 전담
- `backend/`, `docker-compose.yml`, `nginx.conf` — hygrenn 전담
- `frontend/src/types/index.ts`, `.env.example`, `CLAUDE.md` — 양쪽 공동 관리 (수정 전 협의)

---

## 기술 스택

**프론트:** React 18 + TypeScript, Vite, shadcn/ui, Tailwind v4, Zustand, Axios, Lightweight Charts 4, Recharts

**백엔드:** FastAPI, SQLAlchemy 2 + Alembic, PostgreSQL 15, Redis 7, Celery, PyTorch (LSTM), pykrx, python-kis, SendGrid, Docker + Nginx

---

## API Base URL

- 개발: `http://localhost:8000`
- 환경변수: `VITE_API_BASE`
- 전체 엔드포인트 명세: TRD 섹션 5 참고
- 프론트는 백엔드 완성 전까지 mock 데이터로 개발 후 교체

---

## 브랜치 & 작업 흐름

```bash
# 매일 시작
git checkout hwang          # 또는 seogu-Jeong
git pull origin dev         # 상대방 변경사항 반영

# 작업 후
git add .
git commit -m "feat: 내용"
git push origin hwang

# dev merge는 GitHub PR로, merge 전 카톡 알림 필수
```

커밋 prefix: `feat` / `fix` / `refactor` / `style` / `docs` / `chore`

---

## 개발 Phase

Phase 완료 시 dev merge. 상세 작업 목록은 TRD 섹션 15 참고.

- [x] Phase 1: 인증 + 레이아웃 + 기본 API (프론트엔드 완료 2026-06-01)
- [ ] Phase 2: 실시간 시세 + 차트
- [ ] Phase 3: AI 예측 + 시그널
- [ ] Phase 4: 거래 + 포트폴리오 + 시뮬레이터

---

## 로컬 실행

```bash
# 백엔드
docker-compose up -d postgres redis
cd backend && uvicorn main:app --reload --port 8000

# 프론트
cd frontend && npm install && npm run dev
```

`.env.example` 복사해서 `.env` 만들기. `.env`는 절대 커밋 금지.
