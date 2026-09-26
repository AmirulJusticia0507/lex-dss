# Vercel Deployment Guide - Lex-DSS

## Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐
│   Vercel        │     │  Railway/       │
│   (Frontend)    │────▶│  Render/Fly.io  │
│   SPA Build     │     │  (Backend API)  │
└─────────────────┘     └─────────────────┘
                                │
                                ▼
                        ┌─────────────────┐
                        │  Neon PostgreSQL│
                        │  + pgvector     │
                        └─────────────────┘
                                │
                                ▼
                        ┌─────────────────┐
                        │  Ollama Server  │
                        │  (Self-hosted)  │
                        └─────────────────┘
```

**Why separate backend?** Vercel's Python serverless functions have limitations:
- Cold starts with database connection pools
- 10-30s max execution time
- No persistent connections (pgvector needs connection pool)
- No background workers for ingestion

## 1. Backend Deployment (Railway/Render/Fly.io)

### Railway (Recommended - easiest)

1. Create new Railway project → "Deploy from GitHub repo"
2. Select `lex-dss` repo, set **Root Directory** to `backend`
3. Add PostgreSQL database (Railway provides managed Postgres + pgvector)
4. Add Redis (for caching/queue)
5. Set environment variables (see below)
6. Deploy → get backend URL (e.g., `https://lex-dss-api.railway.app`)

### Render

1. New Web Service → Connect GitHub
2. Root Directory: `backend`
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add PostgreSQL + Redis from Render dashboard
6. Set environment variables

### Fly.io

```bash
fly launch --name lex-dss-api --region sin --dockerfile backend/Dockerfile
fly postgres create --name lex-dss-db --region sin
fly redis create --name lex-dss-redis --region sin
fly secrets set < backend/.env.production
fly deploy
```

## 2. Frontend Deployment (Vercel)

### Quick Setup

1. Go to [vercel.com/new](https://vercel.com/new)
2. Import `lex-dss` repository
3. **Framework Preset**: Vite
4. **Root Directory**: `frontend`
5. **Build Command**: `npm run build`
6. **Output Directory**: `dist`
7. Add Environment Variables (see below)
8. Deploy

### Vercel Environment Variables (Dashboard → Settings → Environment Variables)

| Variable | Value | Environment |
|----------|-------|-------------|
| `VITE_API_BASE_URL` | `https://your-backend-url.railway.app/api/v1` | Production, Preview |
| `VITE_APP_NAME` | `Lex-DSS` | All |
| `VITE_APP_VERSION` | `1.0.0` | All |
| `VITE_ENABLE_MOCK_DATA` | `false` | Production, Preview |
| `VITE_ENABLE_ANALYTICS` | `true` | Production |

> **Important**: `VITE_API_BASE_URL` must point to your deployed backend (Railway/Render/Fly.io), NOT Vercel.

## 3. Backend Environment Variables (Railway/Render/Fly.io)

Copy from `backend/.env.example` and set in your platform's dashboard:

```env
# App
APP_NAME=Lex-DSS
APP_VERSION=0.1.0
DEBUG=False
API_V1_STR=/api/v1

# Database (Railway/Render provides these automatically)
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db?sslmode=require

# Security - GENERATE NEW SECRET!
SECRET_KEY=your-64-char-random-secret-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# LLM - Ollama (Primary)
OLLAMA_BASE_URL=http://your-ollama-server:11434
OLLAMA_LLM_MODEL=deepseek-r1:8b
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
OLLAMA_AGENT_MODEL=lex-integrity-agent:latest
OLLAMA_TIMEOUT=120

# LLM - Gemini (Fallback)
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-2.5-flash
GEMINI_EMBEDDING_MODEL=models/embedding-001
GEMINI_TIMEOUT=60

# LLM Settings
LLM_TEMPERATURE=0.2
LLM_MAX_TOKENS=4096
LLM_SYSTEM_PROMPT="Anda adalah asisten hukum Indonesia expert..."

# Embedding
EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=nomic-embed-text
EMBEDDING_DIMENSION=768

# Cache
REDIS_URL=redis://your-redis-host:6379/0

# CORS - MUST include your Vercel frontend URL
CORS_ORIGINS=https://lex-dss.vercel.app,https://your-preview.vercel.app
```

### Generate SECRET_KEY

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

## 4. Ollama Setup (Required for LLM)

### Option A: Railway/Render (same as backend)
Add Ollama as a separate service in your platform

### Option B: Dedicated GPU Server (Recommended for production)
```bash
# On a GPU server (RunPod, Lambda Labs, own hardware)
docker run -d --gpus all -p 11434:11434 -v ollama:/root/.ollama ollama/ollama
ollama pull deepseek-r1:8b
ollama pull nomic-embed-text
ollama pull lex-integrity-agent:latest  # if custom model
```

### Option C: Local Dev Only
```bash
ollama serve
ollama pull deepseek-r1:8b
ollama pull nomic-embed-text
```

## 5. Database Setup (Neon / Managed Postgres)

### Neon (Serverless Postgres + pgvector)
1. Create project at [neon.tech](https://neon.tech)
2. Enable pgvector extension: `CREATE EXTENSION IF NOT EXISTS vector;`
3. Run migrations:
```bash
cd backend
alembic upgrade head
```
4. Seed legal data (if needed)

### Railway/Render Postgres
Same steps - they provide standard Postgres with pgvector support.

## 6. Custom Domain

### Vercel (Frontend)
1. Dashboard → Settings → Domains
2. Add `lex-dss.yourdomain.com`
3. Configure DNS (CNAME to `cname.vercel-dns.com`)

### Backend (Railway/Render)
1. Add custom domain in platform dashboard
2. Update `CORS_ORIGINS` in backend env vars
3. Update `VITE_API_BASE_URL` in Vercel env vars

## 7. CI/CD Pipeline

### GitHub Actions (Optional)
Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy
on:
  push:
    branches: [main]

jobs:
  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: cd frontend && npm ci && npm run build
      - uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          vercel-args: '--prod'
        working-directory: ./frontend

  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: railway-action@v1
        with:
          token: ${{ secrets.RAILWAY_TOKEN }}
          service: lex-dss-api
```

## 8. Verification Checklist

After deployment:

- [ ] Frontend loads at `https://lex-dss.vercel.app`
- [ ] Login works (backend auth)
- [ ] Conflict Checker → analyzes draft → returns results
- [ ] DSS Panel → generates legal opinion
- [ ] Legal Library → searches articles
- [ ] Settings → shows correct API URL
- [ ] CORS errors: none in browser console
- [ ] LLM responses: check Ollama/Gemini logs

## 9. Troubleshooting

| Issue | Solution |
|-------|----------|
| CORS error | Check `CORS_ORIGINS` includes Vercel URL exactly |
| LLM timeout | Increase `OLLAMA_TIMEOUT`, check Ollama server health |
| DB connection failed | Verify `DATABASE_URL` format, check SSL mode |
| Build fails | Check Node version (20+), run `npm ci` locally first |
| 404 on refresh | Ensure Vercel `rewrites` config points to `/index.html` |

## 10. Cost Estimate (Monthly)

| Service | Tier | Est. Cost |
|---------|------|-----------|
| Vercel (Frontend) | Pro | $20 |
| Railway (Backend + DB + Redis) | Hobby/Pro | $5-20 |
| Neon Postgres | Free/Pro | $0-19 |
| Ollama GPU Server | RunPod A100 | ~$50-100 |
| **Total** | | **$75-160** |

---

**Next Steps:**
1. Deploy backend to Railway/Render first
2. Note the backend URL
3. Deploy frontend to Vercel with `VITE_API_BASE_URL` set
4. Configure custom domains
5. Set up monitoring (Sentry, LogRocket)