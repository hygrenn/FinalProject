# 리비전 노트 — 2026-06-18 (정석우)

## 변경 개요
재무 종합 판단 기능 추가, 차트 기간 확장, PR 템플릿 도입, 환경변수 누수 수정

---

## 1. `backend/core/config.py` — `extra: ignore` 추가
- **왜**: `frontend/.env`의 `VITE_API_BASE` 환경변수가 pydantic-settings 2.x 에서
  예상치 못한 필드로 인식돼 `ValidationError` 발생. `"extra": "ignore"` 추가로 수정.
- **영향**: 로컬 개발 환경(`dev_startup.py`)에서 `frontend/.env` 로드 시 오류 방지.

---

## 2. `backend/services/fundamental_service.py` — ROE 지표 추가
- 네이버 금융 통합 API에서 `roe` 필드를 추출.
- ROE가 있을 때 점수 가중치 변경:
  - 기존: PER 45%, PBR 30%, EPS 15%, 배당 10%
  - 변경: PER 35%, PBR 25%, ROE 20%, EPS 12%, 배당 8%
- `metrics` 응답에 `roe` 필드 추가.

---

## 3. `backend/services/comprehensive_service.py` — 신규 종합 판단 서비스
- AI 시그널(40%) + 재무 평가(35%) + 시장 지수(25%) → 0-10점 종합 점수.
- 등급: 강력매수(≥8) / 매수(≥6.5) / 중립(≥5) / 매도주의(≥3.5) / 매도.
- Redis 캐시 5분.
- 각 컴포넌트 점수, 근거 텍스트, 지수 데이터 포함 반환.

---

## 4. `backend/api/routes/analysis.py` — `/analysis/comprehensive/{code}` 엔드포인트 추가
- Rate limit: 30/minute.
- 기존 `/fundamental`, `/recommendations`, `/indices` 엔드포인트 유지.

---

## 5. 차트 기간 확장
- `backend/services/market_service.py`: `5y: 1825` 기간 추가.
- `backend/api/routes/stocks.py`: period 파라미터 패턴에 `3y`, `5y` 허용.
- `frontend/src/components/MainPanel/ChartTab/ChartTab.tsx`:
  - `period` state 추가 (기본값: `1y`).
  - 기간 선택 UI 바 추가 (1개월 / 3개월 / 1년 / 2년 / 3년 / 5년).
  - 분봉 모드에서는 기간 바 숨김.

---

## 6. `frontend/src/components/Analysis/ComprehensivePanel.tsx` — 신규 종합 판단 패널
- 종합 점수 대형 표시, 등급 뱃지.
- AI / 재무 / 시장 컴포넌트 점수 바 (색상: 초록/노랑/빨강).
- 근거 목록.
- `AITab.tsx`에 추가 (FundamentalPanel, RecommendationPanel 상단).

---

## 7. `.github/PULL_REQUEST_TEMPLATE.md` — PR 템플릿 신규
- 변경 유형 체크리스트, 리비전 문서 링크, 개발 확인 항목.
- 앞으로 PR 작성 시 자동 적용.

---

## 참고
- 시세/AI 계산 로직 변경 없음 (ai_service.py 그대로).
- 네이버 모바일 API 엔드포인트 변경 없음.
- 기존 FundamentalPanel / RecommendationPanel 레이아웃 유지, ComprehensivePanel 상단 추가.
