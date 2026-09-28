# Lampiran 2: Diagram Arsitektur Lex-DSS

---

## 1. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        LEX-DSS PLATFORM                             │
│                                                                     │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐      │
│  │   Frontend   │    │   Backend    │    │   AI Engine      │      │
│  │   (Vue.js)   │◄──►│  (FastAPI)   │◄──►│                  │      │
│  │              │    │              │    │  ┌────────────┐  │      │
│  │ - Dashboard  │    │ - REST API   │    │  │ RAG Engine │  │      │
│  │ - Conflict   │    │ - Auth JWT   │    │  │ (LangChain)│  │      │
│  │   Checker    │    │ - Rate Limit │    │  └────────────┘  │      │
│  │ - DSS Panel  │    │ - Audit Log  │    │                  │      │
│  │ - Library    │    │ - Cache      │    │  ┌────────────┐  │      │
│  │              │    │   (Redis)    │    │  │ Deviation  │  │      │
│  └──────────────┘    └──────┬───────┘    │  │  Engine    │  │      │
│                             │            │  └────────────┘  │      │
│                             │            │                  │      │
│                             │            │  ┌────────────┐  │      │
│                             │            │  │  Wealth    │  │      │
│                             │            │  │  Anomaly   │  │      │
│                             │            │  │  Engine    │  │      │
│                             │            │  └────────────┘  │      │
│                             │            │                  │      │
│                             │            │  ┌────────────┐  │      │
│                             │            │  │   Rules    │  │      │
│                             │            │  │  Engine    │  │      │
│                             │            │  │(Lex Integ.)│  │      │
│                             │            │  └────────────┘  │      │
│                             │            └────────┬─────────┘      │
│                             │                     │                │
│                    ┌────────┴─────────────────────┘                │
│                    │                                              │
│                    ▼                                              │
│           ┌────────────────┐                                      │
│           │  PostgreSQL    │                                      │
│           │  + pgvector    │                                      │
│           │                │                                      │
│           │ - legal_articles│                                     │
│           │ - norm_conflicts│                                     │
│           │ - lhkpn_reports │                                     │
│           │ - users         │                                     │
│           │ - audit_logs    │                                     │
│           └────────────────┘                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Data Flow: Wealth Anomaly Detection

```
┌─────────────────┐
│  Data Source    │
│  (LHKPN KPK)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│  Data Ingestion │────►│  Preprocessing  │
│  (Manual/API)   │     │  - Normalisasi  │
└─────────────────┘     │  - Cleaning     │
                        │  - Validasi     │
                        └────────┬────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │   Feature       │
                        │   Engineering   │
                        │                 │
                        │ - Velocity      │
                        │ - Income Ratio  │
                        │ - Peer Compare  │
                        │ - Composition   │
                        └────────┬────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │  Anomaly Model  │
                        │  (Rule-based +  │
                        │   Statistical)  │
                        └────────┬────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │  Risk Score     │
                        │  (0-100)        │
                        └────────┬────────┘
                                 │
                    ┌────────────┼────────────┐
                    │            │            │
                    ▼            ▼            ▼
              ┌──────────┐ ┌──────────┐ ┌──────────┐
              │  GREEN   │ │  YELLOW  │ │   RED    │
              │  (0-29)  │ │  (30-59) │ │  (60-100)│
              └──────────┘ └──────────┘ └──────────┘
                    │            │            │
                    │            │            ▼
                    │            │     ┌──────────────┐
                    │            │     │ Human Review │
                    │            │     │ (Komisi      │
                    │            │     │  Yudisial)   │
                    │            │     └──────────────┘
                    ▼            ▼
              ┌─────────────────────────┐
              │      Dashboard          │
              │      Monitoring         │
              └─────────────────────────┘
```

---

## 3. Security Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Security Layers                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Layer 1: Network Security                              │
│  ├── HTTPS/TLS 1.3                                      │
│  ├── Firewall (Cloudflare)                              │
│  └── DDoS Protection                                    │
│                                                         │
│  Layer 2: Application Security                          │
│  ├── JWT Authentication                                  │
│  ├── Rate Limiting (100 req/min)                        │
│  ├── Input Validation                                   │
│  └── CORS Policy                                        │
│                                                         │
│  Layer 3: Data Security                                 │
│  ├── AES-256 Encryption (at rest)                       │
│  ├── Database Row-Level Security                        │
│  ├── Audit Logging                                      │
│  └── Data Anonymization                                 │
│                                                         │
│  Layer 4: Infrastructure Security                       │
│  ├── Container Isolation (Docker)                       │
│  ├── Secret Management (Environment Variables)          │
│  └── Regular Security Updates                           │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 4. Deployment Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Production Environment                  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────┐      ┌─────────────┐                  │
│  │   Vercel    │      │  Railway    │                  │
│  │  (Frontend) │      │  (Backend)  │                  │
│  │   Vue.js    │      │  FastAPI    │                  │
│  └─────────────┘      └──────┬──────┘                  │
│                              │                          │
│                              ▼                          │
│                       ┌─────────────┐                   │
│                       │   Neon      │                   │
│                       │ PostgreSQL  │                   │
│                       │ + pgvector  │                   │
│                       └─────────────┘                   │
│                                                         │
│  ┌─────────────┐      ┌─────────────┐                  │
│  │   Redis     │      │   Ollama    │                  │
│  │  (Cache)    │      │  (LLM)      │                  │
│  └─────────────┘      └─────────────┘                  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 5. Technology Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Frontend | Vue.js | 3.4 |
| UI Library | Element Plus | 2.6 |
| CSS | TailwindCSS | 3.4 |
| Backend | Python + FastAPI | 3.11+ |
| ORM | SQLAlchemy | 2.0 |
| Database | PostgreSQL | 16 |
| Vector DB | pgvector | 0.5 |
| Cache | Redis | 7.2 |
| LLM | Ollama (deepseek-r1) | 8b |
| Embedding | nomic-embed-text | 768-dim |
| Deployment | Vercel + Railway | - |
