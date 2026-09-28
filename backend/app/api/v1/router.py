from fastapi import APIRouter

from app.api.v1.endpoints import (
    legal_articles,
    norm_conflicts,
    audit,
    deviation,
    auth,
    rag,
    legal_analysis,
    dss,
    ingest,
    analysis,
    users,
    integration,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["User Administration"])
api_router.include_router(legal_articles.router, prefix="/legal-articles", tags=["Legal Articles"])
api_router.include_router(norm_conflicts.router, prefix="/norm-conflicts", tags=["Norm Conflicts"])
api_router.include_router(audit.router, prefix="/audit", tags=["Audit Logs"])
api_router.include_router(deviation.router, prefix="/deviation", tags=["Deviation Scoring"])
api_router.include_router(rag.router, prefix="/rag", tags=["RAG Pipeline"])
api_router.include_router(legal_analysis.router, prefix="/legal", tags=["Legal Analysis"])
api_router.include_router(dss.router, prefix="/dss", tags=["DSS Panel"])
api_router.include_router(ingest.router, prefix="/ingest", tags=["Document Ingestion"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["Lex Integrity Analysis"])
api_router.include_router(integration.router, prefix="/integration", tags=["Lex Integrity Integration"])
# Alias sesuai docs/API_SPECIFICATION.md §4.4-4.5: daftar/detail konflik di bawah /analysis.
api_router.include_router(
    norm_conflicts.router,
    prefix="/analysis/conflicts",
    tags=["Norm Conflicts"],
    include_in_schema=False,
)
