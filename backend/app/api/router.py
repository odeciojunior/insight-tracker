from fastapi import APIRouter
from .endpoints import insights, auth

api_router = APIRouter()

# Add routers
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(insights.router, prefix="/insights", tags=["insights"])
