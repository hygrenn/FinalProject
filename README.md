# StockSenseAI

AI 기반 주식 분석 플랫폼 (FastAPI + React + PostgreSQL + Redis)

## 통합 개발 환경 실행

### 1. 환경 변수 설정 (선택)

```bash
cp .env.example .env
# .env 편집 — SENDGRID_API_KEY, GOOGLE_CLIENT_ID/SECRET, ENCRYPTION_KEY 등
```

`.env`가 없어도 개발 기본값으로 실행되며, 외부 연동 기능을 사용할 때 생성하면 됩니다.

ENCRYPTION_KEY 생성:
```bash
python -c "import base64, os; print(base64.b64encode(os.urandom(32)).decode())"
```

### 2. 전체 서비스 실행

```bash
docker compose up --build
```

Compose가 PostgreSQL, Redis, DB migration, FastAPI, Celery worker, Vite frontend를 함께 실행합니다.

- 프론트엔드: http://localhost:5173
- API 문서: http://localhost:8000/docs
- API 상태 확인: http://localhost:8000/health

종료:

```bash
docker compose down
```

데이터 볼륨까지 초기화:

```bash
docker compose down -v
```

## 로컬 개별 실행

Docker 없이 백엔드와 프론트엔드를 따로 실행할 수도 있습니다.

```bash
cd backend
pip install -r requirements-dev.txt
uvicorn main:app --reload

cd frontend
npm install
npm run dev
```

LSTM 모델 학습/예측까지 사용할 때는 백엔드 의존성을 다음처럼 설치합니다.

```bash
pip install -r backend/requirements-ml.txt
```

### 로컬 예측 생성 후 배포 서버 업로드

배포 백엔드는 PyTorch 없이 DB에 저장된 예측을 제공합니다. 모델 학습과 예측 생성은 로컬에서 실행한 뒤 인증 키로 결과만 업로드합니다.

```bash
cd backend
ML_UPLOAD_KEY=<서버와 동일한 키> python -m ml.generate_predictions \
  --codes 005930,000660 \
  --api-url http://localhost:8000
```

서버의 `.env`에도 동일한 `ML_UPLOAD_KEY`를 설정해야 합니다.

## 테스트

테스트 전 `stocksense_test` DB가 필요합니다:

```bash
# Docker postgres 컨테이너 기준
docker exec -it <postgres-container> psql -U stocksense -c "CREATE DATABASE stocksense_test;"

# 또는 psql 직접 접속
psql -U stocksense -c "CREATE DATABASE stocksense_test;"
```

테스트 실행:

```bash
cd backend
pytest -q
```

## Celery 워커 (선택)

```bash
cd backend
celery -A tasks worker --loglevel=info
```
