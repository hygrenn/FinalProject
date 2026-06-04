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

- [ ] Phase 1: 인증 + 레이아웃 + 기본 API
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

## KIS API 사용 reference codes (참고용)
" reference/ "  폴더에 레퍼런스 코드가 있음. 정확한 정보 필요시 작업 전 관련 파일을 직접 읽어볼 것
reference/access_token_issuance.py     # 접근코드 발급
reference/kis_auth.py                  #
reference/kis_domstk.py                # import할 샘플파일 제공
reference/kis_domstk_current.py        # 주식현재가 시세
reference/kis_domstk_buy.py            # 국내주식 기본시세 > 주식현재가 체결 시세 가져오기
reference/kis_domstk_day.py            # 일자별 시세
reference/kis_domstk_hoga.py           # 호가/예상체결 정보 가져오기
reference/kis_domstk_sise.py           # 국내주식기간별시세(일/주/월/년)
reference/kis_domstk_dangil.py         # 당일시간대별체결 정보
reference/kis_domstk_cash.py           # 주식주문 api 이용, 원하는 종목 매수/매도
reference/kis_domstk_cancel.py         # 주식주문 정정취소
reference/kis_domstk_johwe.py          # 주식정정취소가능주문내역조회
reference/kis_domstk_cur.py            # 주식일별주문체결현황조회
reference/kis_api.py                   # api 호출 샘플
reference/kis_api_test.py              # api 호출 실행
reference/kis_dev.yaml                 
reference/kis_api_responce.py          # api 응답 처리
reference/kis_api_call.py              # api 호출
reference/token_issue.py               # 토큰 발급
reference/token_reissue.py             # 토큰 재발급
reference/hash_generate.py             # 해쉬키 생성