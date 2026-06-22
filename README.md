# StockSenseAI

AI 기반 주식 분석 및 모의/실거래 보조 플랫폼입니다.

프론트엔드는 React + Vite, 백엔드는 FastAPI, 데이터베이스는 PostgreSQL, 캐시는 Redis를 사용합니다. Docker Compose로 전체 개발 환경을 한 번에 실행할 수 있고, 필요하면 백엔드와 프론트엔드를 로컬에서 따로 실행할 수도 있습니다.

## 주요 기능

- 국내 주식 시세, 차트, 호가, 체결 정보 조회
- 관심 종목, 추천 종목, AI 신호, 패턴 분석
- 포트폴리오, 주문 내역, 수익률, 성과 지표 조회
- 모의매매 및 자동매매 실험
- KIS Open API 기반 계좌/시세/주문 연동
- 로컬 LSTM 예측 결과 생성 및 서버 업로드

> 주의: 실거래 모드는 실제 계좌와 주문 API를 사용합니다. `.env`의 `SYSTEM_KIS_MODE=real` 설정 전에는 반드시 기능 동작과 주문 경로를 확인하세요.

## 요구 사항

- Docker Desktop 또는 Colima + Docker Compose
- Node.js 22 이상, 로컬 프론트 실행 시 필요
- Python 3.11 이상, 로컬 백엔드 실행 시 필요
- 한국투자증권 Open API 키, KIS 연동 기능 사용 시 필요

## 처음 받은 뒤 준비

프로젝트 폴더로 이동합니다. 아래 예시의 `FinalProject`는 clone한 저장소 폴더명이며, 다른 이름으로 받은 경우 해당 폴더명으로 바꾸면 됩니다.

```bash
cd FinalProject
```

공식 KIS 참조 저장소가 submodule로 연결되어 있으므로 처음 clone한 경우 초기화합니다.

```bash
git submodule update --init --recursive
```

환경 변수 파일을 만듭니다.

```bash
cp .env.example .env
```

## .env 설정

`.env`는 프로젝트 루트에 둡니다.

```text
FinalProject/
  .env
  docker-compose.yml
  backend/
  frontend/
```

개발용 최소 예시는 다음과 같습니다.

```env
APP_ENV=development
SECRET_KEY=change-this-local-dev-secret-min-32-chars
ENCRYPTION_KEY=생성한_base64_키

POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=stocksense
POSTGRES_TEST_DB=stocksense_test
POSTGRES_USER=stocksense
POSTGRES_PASSWORD=stocksense
DATABASE_URL=postgresql+asyncpg://stocksense:stocksense@localhost:5432/stocksense

REDIS_URL=redis://localhost:6379/0

CORS_ORIGINS=http://localhost:5173
FRONTEND_URL=http://localhost:5173
VITE_API_BASE=http://localhost:8000

SENDGRID_API_KEY=
FROM_EMAIL=noreply@stocksense.ai

GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback

ML_UPLOAD_KEY=

SYSTEM_KIS_APP_KEY=
SYSTEM_KIS_APP_SECRET=
SYSTEM_KIS_MODE=paper
SYSTEM_KIS_ACCOUNT_NO=
```

`ENCRYPTION_KEY`는 32바이트 base64 문자열이어야 합니다. 아래 명령으로 생성합니다.

```bash
python -c "import os,base64; print(base64.b64encode(os.urandom(32)).decode())"
```

생성된 값을 `.env`에 넣습니다.

```env
ENCRYPTION_KEY=여기에_생성된_값
```

### 주요 환경 변수 설명

| 변수 | 설명 |
| --- | --- |
| `APP_ENV` | `development`이면 로컬 개발 모드로 동작합니다. |
| `SECRET_KEY` | JWT, 세션, 이메일 인증 토큰 서명에 사용합니다. |
| `ENCRYPTION_KEY` | KIS 키 등 민감정보 암호화에 사용합니다. 반드시 32바이트 base64 값이어야 합니다. |
| `POSTGRES_*` | Docker PostgreSQL 계정, DB 이름, 테스트 DB 이름입니다. |
| `DATABASE_URL` | 로컬 백엔드 실행 시 사용할 DB URL입니다. Docker backend에서는 compose가 컨테이너용 URL로 덮어씁니다. |
| `REDIS_URL` | 로컬 실행 시 사용할 Redis URL입니다. Docker backend에서는 `redis://redis:6379/0`으로 덮어씁니다. |
| `CORS_ORIGINS` | 프론트엔드 접속 주소입니다. 기본값은 `http://localhost:5173`입니다. |
| `FRONTEND_URL` | 이메일 인증/Google OAuth 리다이렉트에 사용합니다. |
| `VITE_API_BASE` | 프론트엔드가 호출할 백엔드 주소입니다. |
| `SENDGRID_API_KEY` | 이메일 인증 발송에 사용합니다. 비워두면 로컬 개발에서는 이메일 인증을 생략합니다. |
| `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` | Google 로그인 사용 시 필요합니다. |
| `ML_UPLOAD_KEY` | 로컬에서 만든 예측 결과를 API로 업로드할 때 사용하는 인증 키입니다. |
| `SYSTEM_KIS_APP_KEY`, `SYSTEM_KIS_APP_SECRET` | 한국투자증권 Open API 키입니다. |
| `SYSTEM_KIS_ACCOUNT_NO` | KIS 계좌번호입니다. 예: `12345678-01` |
| `SYSTEM_KIS_MODE` | `paper` 또는 `real`. 기본은 `paper`입니다. |

브라우저는 가능하면 아래 주소로 접속하세요.

```text
http://localhost:5173
```

`http://127.0.0.1:5173`로 접속하면 `CORS_ORIGINS`와 달라 로그인 요청이 막힐 수 있습니다. 127.0.0.1도 허용하려면 다음처럼 설정합니다.

```env
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

## Docker로 전체 실행

가장 권장하는 실행 방법입니다.

```bash
cd FinalProject
docker compose up -d --build
```

이 명령은 다음 서비스를 실행합니다.

- `postgres`: PostgreSQL
- `redis`: Redis
- `db-init`: 테스트 DB 생성
- `migrate`: Alembic DB migration
- `backend`: FastAPI 서버
- `frontend`: Vite 개발 서버
- `celery`: 백그라운드 작업 worker
- `celery-beat`: 주기 작업 scheduler

실행 확인:

```bash
docker compose ps
```

접속 주소:

- 프론트엔드: http://localhost:5173
- 백엔드 API 문서: http://localhost:8000/docs
- 백엔드 상태 확인: http://localhost:8000/health

로그 확인:

```bash
docker compose logs -f backend
docker compose logs -f frontend
```

종료:

```bash
docker compose down
```

DB 데이터까지 모두 삭제하며 종료:

```bash
docker compose down -v
```

`down -v`는 계정, 포트폴리오, 거래 기록 등 PostgreSQL volume 데이터를 삭제합니다.

## Docker로 자주 쓰는 실행 명령

인프라만 먼저 켜기:

```bash
docker compose up -d postgres redis
```

백엔드와 프론트엔드 실행:

```bash
docker compose up -d backend frontend
```

백엔드만 재시작:

```bash
docker compose restart backend
```

프론트엔드만 재시작:

```bash
docker compose restart frontend
```

의존성이나 Dockerfile이 바뀐 뒤 백엔드 재빌드:

```bash
docker compose up -d --build backend
```

의존성이나 Dockerfile이 바뀐 뒤 프론트엔드 재빌드:

```bash
docker compose up -d --build frontend
```

최신 dev를 pull한 뒤 프론트 의존성이 추가되어 Vite import 에러가 날 경우:

```bash
docker compose exec frontend npm install
docker compose restart frontend
```

예를 들어 `Failed to resolve import "@radix-ui/react-switch"` 같은 에러는 Docker volume의 `/app/node_modules`가 최신 `package.json`을 따라오지 못한 경우가 많습니다.

## Docker 실행 시 DB 동작

`docker-compose.yml`은 PostgreSQL 데이터를 `pgdata` volume에 저장합니다. 따라서 컨테이너를 재시작해도 DB 데이터는 유지됩니다.

```bash
docker compose restart backend
docker compose restart frontend
```

위 명령으로는 DB가 초기화되지 않습니다.

DB를 완전히 초기화하려면 다음을 실행합니다.

```bash
docker compose down -v
docker compose up -d --build
```

주의: `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`는 PostgreSQL volume이 처음 만들어질 때 반영됩니다. 이미 volume이 만들어진 뒤 `.env`의 DB 계정이나 비밀번호를 바꾸면 인증 실패가 날 수 있습니다. 기존 데이터를 유지하려면 `.env`를 volume 생성 당시 값으로 되돌리고, 초기화해도 괜찮으면 `docker compose down -v`를 사용하세요.

## 로컬에서 백엔드 실행

Docker PostgreSQL과 Redis는 그대로 사용하고, 백엔드만 로컬 Python으로 실행할 수 있습니다.

먼저 인프라를 켭니다.

```bash
cd FinalProject
docker compose up -d postgres redis
docker compose run --rm db-init
docker compose run --rm migrate
```

백엔드 가상환경을 만들고 실행합니다.

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn main:app --reload --port 8000
```

백엔드 주소:

```text
http://localhost:8000
```

백엔드를 다시 시작하려면 실행 중인 터미널에서 `Ctrl + C`를 누른 뒤 다시 실행합니다.

```bash
uvicorn main:app --reload --port 8000
```

## 로컬에서 프론트엔드 실행

프론트엔드만 로컬 Node.js로 실행할 수 있습니다.

```bash
cd frontend
npm install
npm run dev
```

프론트엔드 주소:

```text
http://localhost:5173
```

프론트엔드가 호출할 백엔드 주소는 `frontend/.env` 또는 루트 `.env`의 `VITE_API_BASE`로 맞춥니다.

```env
VITE_API_BASE=http://localhost:8000
```

## 로컬 전체 실행 순서

Docker를 DB/Redis 용도로만 사용하고 앱은 로컬에서 실행할 때는 터미널을 3개 사용합니다.

터미널 1:

```bash
cd FinalProject
docker compose up -d postgres redis
docker compose run --rm db-init
docker compose run --rm migrate
```

터미널 2:

```bash
cd backend
source .venv/bin/activate
uvicorn main:app --reload --port 8000
```

터미널 3:

```bash
cd frontend
npm run dev
```

접속:

```text
http://localhost:5173
```

## KIS Open API 설정

KIS 연동 기능을 사용하려면 `.env`에 아래 값을 채웁니다.

```env
SYSTEM_KIS_APP_KEY=발급받은_APP_KEY
SYSTEM_KIS_APP_SECRET=발급받은_APP_SECRET
SYSTEM_KIS_ACCOUNT_NO=12345678-01
SYSTEM_KIS_MODE=paper
```

`SYSTEM_KIS_MODE`:

- `paper`: 모의투자/모의계좌 기준
- `real`: 실제 계좌/실거래 기준

실거래 모드는 실제 주문이 발생할 수 있으므로 데모나 개발 중에는 `paper`를 권장합니다.

KIS 키가 없으면 일부 시세/계좌/주문 기능은 제한됩니다. 이 경우에도 기본 회원가입, 로그인, 차트, 일부 분석 화면은 실행할 수 있습니다.

## 이메일 인증과 Google 로그인

로컬 개발에서 `SENDGRID_API_KEY`가 비어 있으면 이메일 인증을 생략하고 가입 계정을 바로 활성화합니다.

실제 이메일 인증을 사용하려면:

```env
SENDGRID_API_KEY=sendgrid_key
FROM_EMAIL=noreply@example.com
FRONTEND_URL=http://localhost:5173
```

Google 로그인을 사용하려면:

```env
GOOGLE_CLIENT_ID=google_client_id
GOOGLE_CLIENT_SECRET=google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback
FRONTEND_URL=http://localhost:5173
```

## AI 예측 생성과 업로드

Docker 백엔드 기본 의존성에는 PyTorch를 포함하지 않습니다. 이미지 크기와 빌드 시간을 줄이기 위해 LSTM 학습/예측은 로컬에서 실행하고, 결과만 서버 DB에 업로드하는 구조입니다.

ML 의존성이 필요하면 로컬에서 별도로 설치합니다.

```bash
cd FinalProject
pip install -r backend/requirements-ml.txt
```

예측 결과 업로드용 키를 `.env`에 설정합니다.

```env
ML_UPLOAD_KEY=임의의_긴_랜덤_문자열
```

로컬에서 예측을 생성하고 실행 중인 API로 업로드합니다.

```bash
cd backend
ML_UPLOAD_KEY=위와_같은_키 python -m ml.generate_predictions \
  --codes 005930,000660 \
  --api-url http://localhost:8000
```

## 테스트

Docker backend 컨테이너를 사용해 전체 테스트를 실행합니다.

```bash
cd FinalProject
docker compose run --rm \
  -v "$PWD:/project" \
  -w /project \
  -e PYTHONPATH=/project/backend \
  backend sh -c 'pip install --no-cache-dir -r backend/requirements-dev.txt >/tmp/test-deps.log && pytest -q tests'
```

프론트엔드 테스트:

```bash
cd frontend
npm test -- --run
```

프론트엔드 lint:

```bash
npm run lint
```

프론트엔드 production build 확인:

```bash
npm run build
```

## 문제 해결

### 로그인 요청이 CORS로 막힐 때

브라우저 주소가 `http://localhost:5173`인지 확인합니다. `127.0.0.1`로 접속하면 기본 CORS 설정과 달라질 수 있습니다.

필요하면 `.env`를 다음처럼 수정하고 백엔드를 재시작합니다.

```env
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

```bash
docker compose restart backend
```

### 프론트에서 import 에러가 날 때

최신 코드를 pull했는데 프론트 Docker volume의 `node_modules`가 오래된 경우입니다.

```bash
docker compose exec frontend npm install
docker compose restart frontend
```

### DB 계정이 사라진 것처럼 보일 때

대부분 DB가 사라진 것이 아니라 다른 DB URL을 보고 있거나, `docker compose down -v`로 volume이 삭제된 경우입니다.

현재 컨테이너 상태:

```bash
docker compose ps
```

DB 초기화 여부가 괜찮다면:

```bash
docker compose down -v
docker compose up -d --build
```

### KIS API 키 오류가 날 때

아래 값이 루트 `.env`에 있는지 확인합니다.

```env
SYSTEM_KIS_APP_KEY=
SYSTEM_KIS_APP_SECRET=
SYSTEM_KIS_ACCOUNT_NO=
SYSTEM_KIS_MODE=paper
```

수정 후 백엔드를 재시작합니다.

```bash
docker compose restart backend
```

### 포트가 이미 사용 중일 때

8000번 또는 5173번 포트를 다른 프로세스가 사용 중인지 확인합니다.

```bash
lsof -nP -iTCP:8000 -sTCP:LISTEN
lsof -nP -iTCP:5173 -sTCP:LISTEN
```

Docker 환경만 사용할 때는 같은 포트를 쓰는 로컬 `uvicorn`이나 `npm run dev`를 종료하세요.

## 유용한 명령 모음

```bash
# 전체 실행
docker compose up -d --build

# 상태 확인
docker compose ps

# 백엔드 로그
docker compose logs -f backend

# 프론트 로그
docker compose logs -f frontend

# 백엔드 재시작
docker compose restart backend

# 프론트 재시작
docker compose restart frontend

# 전체 종료
docker compose down

# DB 포함 전체 초기화
docker compose down -v
```
