from fastapi import APIRouter

from app.api.v1.endpoints import (
    legal_articles,
    norm_conflicts,
    audit,
    deviation,
    auth,
    rag,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(legal_articles.router, prefix="/legal-articles", tags=["Legal Articles"])
api_router.include_router(norm_conflicts.router, prefix="/norm-conflicts", tags=["Norm Conflicts"])
api_router.include_router(audit.router, prefix="/audit", tags=["Audit Logs"])
api_router.include_router(deviation.router, prefix="/deviation", tags=["Deviation Scoring"])
api_router.include_router(rag.router, prefix="/rag", tags=["RAG Pipeline"])