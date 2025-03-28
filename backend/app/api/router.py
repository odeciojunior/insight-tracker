from fastapi import APIRouter
from .endpoints import auth, insights, relationships, ai_assistant, docs

api_router = APIRouter()

# Include specific endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(insights.router, prefix="/insights", tags=["Insights"])
api_router.include_router(relationships.router, prefix="/relationships", tags=["Relationships"])
api_router.include_router(ai_assistant.router, prefix="/ai", tags=["AI Assistant"])
api_router.include_router(docs.router, prefix="/docs", tags=["Documentation"])
