from fastapi import APIRouter
from .endpoints import insights

api_router = APIRouter()

# Add routers
api_router.include_router(insights.router, prefix="/insights", tags=["insights"])
