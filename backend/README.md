# Lex-DSS Backend

Backend API untuk Lex Decision Support System (Lex-DSS) - Sistem Pendukung Keputusan Berbasis AI untuk Analisis Hukum Indonesia.

## Teknologi

- **Framework**: FastAPI 0.109
- **Database**: PostgreSQL 16 + pgvector
- **ORM**: SQLAlchemy 2.0 (Async)
- **Migrasi**: Alembic
- **Auth**: JWT (python-jose) + bcrypt (passlib)
- **AI/ML**: LangChain, LlamaIndex, OpenAI API
- **Vector Search**: pgvector (1536 dimensi)

## Struktur Project

```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/     # API endpoints
│   │       └── router.py      # Main router
│   ├── core/
│   │   ├── config.py          # Settings & config
│   │   ├── database.py        # DB connection & session
│   │   └── security.py        # JWT & password hashing
│   ├── engine/
│   │   ├── lex_integrity.py   # Lex Integrity rules engine
│   │   ├── rag.py             # RAG pipeline
│   │   └── deviation.py       # Deviation scoring engine
│   ├── models/
│   │   ├── legal.py           # Legal hierarchy, articles, conflicts
│   │   ├── audit.py           # Audit logs, deviation reports
│   │   └── user.py            # User model
│   ├── services/
│   │   └── legal_domains.py   # HTN, Criminal, Civil law services
│   └── main.py                # FastAPI app entry point
├── alembic/
│   ├── env.py                 # Alembic config
│   ├── alembic.ini
│   └── versions/              # Migration scripts
├── requirements.txt
├── pyproject.toml
├── docker-compose.yml
├── Dockerfile
└── .env.example
```

## Quickstart

### 1. Environment Setup

```bash
cd backend
cp .env.example .env
# Edit .env dengan konfigurasi Anda
```

### 2. Database (PostgreSQL + pgvector)

**Local Development (Docker Compose):**
```bash
docker-compose up -d postgres redis
```
Default credentials:
- Host: `localhost`
- Port: `5432`
- User: `postgres`
- Password: `postgres`
- Database: `lex_dss`
- Connection URL: `postgresql+asyncpg://postgres:postgres@localhost:5432/lex_dss`

**Production (Neon PostgreSQL):**
```bash
# Set DATABASE_URL di .env atau environment variable
DATABASE_URL=postgresql+asyncpg://neondb_owner:npg_IfWBbCGaL8O2@ep-polished-unit-b51c91ak-pooler.c-7.us-east-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require
```
> **Note:** Untuk Neon, gunakan `postgresql+asyncpg://` scheme dan pastikan `sslmode=require` disertakan.

**Atau install lokal dengan pgvector extension.**

### 3. Install Dependencies

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Run Migrations

```bash
alembic upgrade head
```

### 4a. Bootstrap Administrator

After the database is configured and migrated, create the first administrator from the backend directory:

```bash
python scripts/create_admin.py admin@example.org
```

The script prompts for the password without echoing it. Public registration creates only `user` accounts; only an administrator can assign the `auditor` or `admin` role.

### 5. Seed Initial Data (Optional)

```bash
# Data hierarki hukum sudah di-seed via migration 001
python scripts/seed_core_laws.py --apply

# Alternatif SQL manual:
# psql "$DATABASE_URL" -f data/legal-seed/core-laws.sql
```

### 6. Run Server

```bash
uvicorn app.main:app --reload
```

Server berjalan di: http://localhost:8000

- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register user
- `POST /api/v1/auth/login` - Login & get JWT token
- `GET /api/v1/auth/me` - Current user profile
- `GET /api/v1/auth/profile` - Current user profile
- `PATCH /api/v1/auth/profile` - Update own name, email, or institution
- `PUT /api/v1/auth/password` - Change own password
- `GET/PUT/DELETE /api/v1/auth/preferences` - Read, save, or clear own settings
- `/api/v1/users` - Admin-only account CRUD and role/permission listing

### Legal Articles
- `POST /api/v1/legal-articles/hierarchy` - Create hierarchy type
- `GET /api/v1/legal-articles/hierarchy` - List hierarchy types
- `POST /api/v1/legal-articles/` - Create legal article
- `GET /api/v1/legal-articles/` - List articles (paginated, filterable)
- `GET /api/v1/legal-articles/{id}` - Get article detail
- `PATCH /api/v1/legal-articles/{id}` - Update article
- `DELETE /api/v1/legal-articles/{id}` - Delete article

### Norm Conflicts (Lex Integrity)
- `POST /api/v1/norm-conflicts/` - Create conflict record
- `GET /api/v1/norm-conflicts/` - List conflicts (filterable)
- `GET /api/v1/norm-conflicts/{id}` - Get conflict detail
- `DELETE /api/v1/norm-conflicts/{id}` - Delete conflict

### Audit Logs (Transparency)
- `POST /api/v1/audit/` - Create audit log
- `GET /api/v1/audit/` - List audit logs
- `GET /api/v1/audit/{id}` - Get audit log detail
- `GET /api/v1/audit/deviations/summary` - Deviation statistics

### Deviation Scoring (DAS)
- `POST /api/v1/deviation/score` - Calculate deviation score
- `POST /api/v1/deviation/reports` - Create deviation report
- `GET /api/v1/deviation/reports` - List reports
- `GET /api/v1/deviation/reports/{id}` - Get report detail
- `GET /api/v1/deviation/reports/stats/summary` - Risk level statistics

### RAG Pipeline
- `POST /api/v1/rag/search` - Semantic search legal articles
- `POST /api/v1/rag/embedding` - Generate embedding for text
- `POST /api/v1/rag/articles/{id}/embedding` - Update article embedding
- `POST /api/v1/rag/articles/batch-embeddings` - Batch update embeddings

## Core Engines

### Lex Integrity Engine
Deteksi kontradiksi norma berdasarkan:
- **Lex Superior**: Hierarki perundang-undangan (Pasal 7 UU 12/2011)
- **Lex Specialis**: Aturan khusus vs umum
- **Lex Posterior**: Aturan baru vs lama
- **Direct Contradiction**: Kontradiksi langsung

### Deviation Alert System (DAS)
Scoring deviasi putusan (0-100):
- **Hierarchy Violation** (35%): Pelanggaran hierarki norma
- **Jurisprudence Anomaly** (25%): Penyimpangan dari yurisprudensi
- **Evidence Gap** (25%): Kesenjangan unsur hukum vs amar
- **Procedural Flaw** (15%): Cacat prosedural/AUPB

Risk Levels:
- **GREEN** (0-29): Selaras dengan logika hukum murni
- **YELLOW** (30-59): Anomali moderat, perlu catatan pengawasan
- **RED** (60-100): HIGH RISK, auto-flag ke Komisi Yudisial

### RAG Pipeline
- Semantic search dengan pgvector
- Hybrid search (vector + keyword)
- Batch embedding generation

## Legal Domain Services

### HTN Service (`HTNService`)
- Validasi hierarki perundang-undangan
- Cek Lex Superior/Lex Specialis/Lex Posterior

### Criminal Law Service (`CriminalLawService`)
- Analisis Anatomie Van Delict (unsur obyektif/subjektif)
- Cek overlapping penalty (ne bis in idem)

### Civil Law Service (`CivilLawService`)
- Validasi syarat sah perjanjian (Pasal 1320 KUHPerdata)
- Deteksi klausula exoneration (Pasal 1337 KUHPerdata)
- Cek klausula baku tidak adil

## Development

### Code Quality

```bash
# Linting
ruff check .

# Formatting
black .
isort .

# Type checking
mypy .
```

### Testing

```bash
pytest tests/ -v --cov=app
```

### New Migration

```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `POSTGRES_SERVER` | Database host (local) | localhost |
| `POSTGRES_PORT` | Database port (local) | 5432 |
| `POSTGRES_USER` | Database user (local) | postgres |
| `POSTGRES_PASSWORD` | Database password (local) | postgres |
| `POSTGRES_DB` | Database name (local) | lex_dss |
| `DATABASE_URL` | Full connection string (production/override) | - |
| `SECRET_KEY` | JWT secret key | (required) |
| `OPENAI_API_KEY` | OpenAI API key | (required for embeddings) |
| `EMBEDDING_MODEL` | OpenAI embedding model | text-embedding-3-small |
| `LLM_MODEL` | OpenAI LLM model | gpt-4-turbo-preview |

**Production DATABASE_URL example (Neon):**
```
postgresql+asyncpg://neondb_owner:npg_IfWBbCGaL8O2@ep-polished-unit-b51c91ak-pooler.c-7.us-east-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require
```

## Deployment

```bash
# Build image
docker build -t lex-dss-backend .

# Run with docker-compose
docker-compose up -d
```

## License

Proprietary - Lex-DSS Team
