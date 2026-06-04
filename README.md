# StockSenseAI

AI 기반 주식 분석 플랫폼 (FastAPI + React + PostgreSQL + Redis)

## 빠른 시작

### 1. 환경 변수 설정

```bash
cp .env.example .env
# .env 편집 — SENDGRID_API_KEY, GOOGLE_CLIENT_ID/SECRET, ENCRYPTION_KEY 등
```

ENCRYPTION_KEY 생성:
```bash
python -c "import base64, os; print(base64.b64encode(os.urandom(32)).decode())"
```

### 2. 인프라 실행

```bash
docker-compose up -d postgres redis
```

### 3. 의존성 설치

```bash
cd backend
pip install -r requirements.txt
# 주의: bcrypt==4.2.0 필수 (5.x는 passlib 1.7.4와 호환 안 됨)
```

### 4. DB 마이그레이션

```bash
# 프로젝트 루트에서 실행 (alembic.ini 위치)
alembic upgrade head
```

### 5. 백엔드 실행

```bash
cd backend
uvicorn main:app --reload
```

API 문서: http://localhost:8000/docs

### 6. 프론트엔드 실행

```bash
cd frontend
npm install
npm run dev
```

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
