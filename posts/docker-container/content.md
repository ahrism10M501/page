# Docker로 재현 가능한 개발 환경 만들기

"내 컴퓨터에선 되는데"를 없애는 가장 확실한 방법은 Docker입니다.

## 컨테이너 vs 가상머신

VM은 OS 전체를 가상화하지만, 컨테이너는 호스트 커널을 공유하면서 프로세스를 격리합니다. 훨씬 가볍고 빠릅니다.

```
VM:        [App] [Libs] [Guest OS] [Hypervisor] [Host OS]
Container: [App] [Libs] [Container Runtime]     [Host OS]
```

## Dockerfile 작성

```dockerfile
# 베이스 이미지 — 구체적인 버전 고정
FROM python:3.12-slim

# 작업 디렉토리 설정
WORKDIR /app

# 의존성 먼저 복사 (레이어 캐시 활용)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 코드 복사
COPY . .

# 비루트 사용자로 실행 (보안)
RUN useradd -m appuser
USER appuser

EXPOSE 8000
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0"]
```

## 레이어 캐시 전략

Dockerfile 명령어 순서가 빌드 속도에 큰 영향을 미칩니다.

```dockerfile
# 나쁜 예: 코드 변경 시 pip install도 재실행
COPY . .
RUN pip install -r requirements.txt

# 좋은 예: requirements.txt 변경 없으면 pip install 캐시 재사용
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
```

## Docker Compose로 멀티 서비스

```yaml
# docker-compose.yml
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/mydb
    depends_on:
      db:
        condition: service_healthy

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
      POSTGRES_DB: mydb
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user"]
      interval: 5s
      timeout: 5s
      retries: 5
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```

## 자주 쓰는 명령어

```bash
# 빌드 & 실행
docker build -t myapp .
docker run -p 8000:8000 myapp

# Compose
docker compose up -d       # 백그라운드 실행
docker compose logs -f app # 로그 팔로우
docker compose down -v     # 볼륨 포함 삭제

# 디버깅
docker exec -it <container_id> bash
docker inspect <container_id>
```

## .dockerignore

빌드 컨텍스트에서 불필요한 파일을 제외합니다.

```
.git
.venv
__pycache__
*.pyc
.env
node_modules
```

## 이미지 크기 줄이기

- `slim` 또는 `alpine` 베이스 이미지 사용
- 멀티 스테이지 빌드로 빌드 도구 제외
- `--no-cache-dir` 플래그로 pip 캐시 제거
