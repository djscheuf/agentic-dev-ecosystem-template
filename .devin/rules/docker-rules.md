---
applies_to:
  - "src/**/Dockerfile*"
  - "src/**/docker-compose*.yml"
  - "src/**/.dockerignore"
---

# Docker Standards

## Core Principles

- Build minimal, secure images
- One process per container
- Containers ephemeral and stateless
- Never store secrets in images
- Use multi-stage builds for production
- Name by intent, not implementation

## Naming Conventions

### Files and Services

| Item | Format | Example |
|------|--------|---------|
| Dockerfile | `Dockerfile.purpose` | `Dockerfile.admin` |
| Docker Compose | `docker-compose.purpose.yml` | `docker-compose.e2e.yml` |
| Container | `project-purpose` | `myapp-admin` |
| Volume | `project-purpose-data` | `myapp-database-data` |
| Network | `project-purpose-network` | `myapp-app-network` |
| Environment Variable | `SCREAMING_SNAKE_CASE` | `API_BASE_URL` |
| Build Argument | `SCREAMING_SNAKE_CASE` | `NODE_VERSION` |
| Multi-Stage Name | `purpose` | `dependencies`, `builder`, `runner` |

### Examples

```dockerfile
# Multi-stage naming
FROM node:18-alpine AS dependencies
FROM node:18-alpine AS builder
FROM nginx:alpine AS production

# Environment variables - descriptive
ENV API_BASE_URL=http://api:3000
ENV DATABASE_CONNECTION_STRING=postgresql://...
ENV MAX_UPLOAD_SIZE=5000000

# Build arguments - descriptive
ARG NODE_VERSION=18
ARG BUILD_ENVIRONMENT=production
```

## Base Images

```dockerfile
# Use specific version tags
FROM node:20.10-alpine3.18
FROM python:3.12-slim-bookworm

# Pin digest for production
FROM node:20.10-alpine3.18@sha256:abc123...

# Multi-stage: SDK for build, runtime for production
FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
FROM mcr.microsoft.com/dotnet/aspnet:8.0 AS runtime
```

## Layer Optimization

```dockerfile
# Single layer with cleanup
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
```

## Cache-Efficient Ordering

Order from least to most frequently changing:

```dockerfile
FROM node:20-alpine
RUN apk add --no-cache tini

RUN addgroup -g 1001 appgroup && \
    adduser -u 1001 -G appgroup -D appuser

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --only=production

COPY --chown=appuser:appgroup . .

USER appuser
EXPOSE 3000
ENTRYPOINT ["/sbin/tini", "--"]
CMD ["node", "server.js"]
```

## Multi-Stage Builds

### Node.js

```dockerfile
FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production

RUN addgroup -g 1001 nodejs && \
    adduser -u 1001 -G nodejs -D nextjs

COPY --from=builder --chown=nextjs:nodejs /app/dist ./dist
COPY --from=builder --chown=nextjs:nodejs /app/node_modules ./node_modules
COPY --from=builder --chown=nextjs:nodejs /app/package.json ./

USER nextjs
EXPOSE 3000
CMD ["node", "dist/server.js"]
```

### Python

```dockerfile
FROM python:3.12-slim-bookworm AS builder
WORKDIR /app
RUN pip install --no-cache-dir poetry==1.7.1
COPY pyproject.toml poetry.lock ./
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes
COPY . .
RUN poetry build --format wheel

FROM python:3.12-slim-bookworm AS runner
WORKDIR /app
RUN groupadd -g 1001 appgroup && useradd -u 1001 -g appgroup -m appuser
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --from=builder /app/dist/*.whl .
RUN pip install --no-cache-dir *.whl && rm *.whl

USER appuser
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### .NET

```dockerfile
FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src
COPY ["src/Api/Api.csproj", "src/Api/"]
COPY ["src/Domain/Domain.csproj", "src/Domain/"]
RUN dotnet restore "src/Api/Api.csproj"
COPY . .
RUN dotnet publish "src/Api/Api.csproj" -c Release -o /app/publish --no-restore

FROM mcr.microsoft.com/dotnet/aspnet:8.0 AS runner
WORKDIR /app
RUN groupadd -g 1001 appgroup && useradd -u 1001 -g appgroup -m appuser
COPY --from=build --chown=appuser:appgroup /app/publish .

USER appuser
EXPOSE 8080
ENTRYPOINT ["dotnet", "Api.dll"]
```

## Security

### Non-Root User

```dockerfile
RUN groupadd -r appgroup && useradd -r -g appgroup appuser
COPY --chown=appuser:appgroup . /app
USER appuser
```

### Minimal Images

```dockerfile
# Remove unnecessary packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends required-package && \
    apt-get purge -y --auto-remove && \
    rm -rf /var/lib/apt/lists/*

# Use distroless
FROM gcr.io/distroless/nodejs20-debian12
```

### No Secrets

```dockerfile
# NEVER
ENV API_KEY=secret123
COPY .env /app/.env

# Use runtime environment variables or secrets management
```

### Read-Only Filesystem

```yaml
security_opt:
  - no-new-privileges:true
read_only: true
tmpfs:
  - /tmp
```

## Docker Compose

### Development

```yaml
version: "3.9"

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
      target: development
    volumes:
      - .:/app:cached
      - /app/node_modules
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=development
      - DATABASE_URL=postgres://postgres:postgres@db:5432/app_dev
    depends_on:
      db:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  db:
    image: postgres:16-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=app_dev
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
```

### Production Override

```yaml
version: "3.9"

services:
  api:
    build:
      target: production
    volumes: []
    environment:
      - NODE_ENV=production
    deploy:
      resources:
        limits:
          cpus: "1.0"
          memory: 512M
        reservations:
          cpus: "0.25"
          memory: 128M
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

## .dockerignore

```dockerignore
.git
.gitignore
.idea
.vscode
*.swp
node_modules
__pycache__
*.pyc
.venv
venv
dist
build
*.egg-info
coverage
.coverage
.pytest_cache
docs
*.md
!README.md
.env
.env.*
*.pem
*.key
Dockerfile*
docker-compose*
.DS_Store
*.log
logs
```

## Health Checks

```dockerfile
# Node.js
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD node healthcheck.js || exit 1

# Python
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Alpine (wget)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/health || exit 1
```

### Health Endpoint

```typescript
app.get("/health", (req, res) => {
  const healthcheck = {
    status: "healthy",
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    checks: { database: "ok", redis: "ok" },
  };
  try {
    res.status(200).json(healthcheck);
  } catch (error) {
    healthcheck.status = "unhealthy";
    res.status(503).json(healthcheck);
  }
});
```

## Tagging Strategy

```bash
# Semantic versioning
myapp:1.0.0
myapp:1.0
myapp:1

# Git-based
myapp:main-abc1234
myapp:feature-xyz-def5678

# Environment-based
myapp:staging
myapp:production

# Never use 'latest' in production
```

## Resource Limits

```yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: "2.0"
          memory: 1G
        reservations:
          cpus: "0.5"
          memory: 256M
```

## Logging

```yaml
services:
  api:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "5"
```

## Network Isolation

```yaml
services:
  api:
    networks:
      - frontend
      - backend
  db:
    networks:
      - backend
  nginx:
    networks:
      - frontend
    ports:
      - "80:80"

networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true
```

## Forbidden Practices

- ❌ Never use `latest` tag in production
- ❌ Never store secrets in images or Dockerfiles
- ❌ Never run containers as root in production
- ❌ Never expose unnecessary ports
- ❌ Never skip health checks in production
- ❌ Never use `COPY . .` before installing dependencies
- ❌ Never ignore .dockerignore file
- ❌ Never hardcode environment-specific values
- ❌ Never use ADD when COPY suffices
- ❌ Never leave package manager caches
- ❌ Never use generic names (`stage1`, `URL`, `DB`)
