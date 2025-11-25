"""
API v1 Router
Aggregates all API endpoints under versioned prefix.
"""
from fastapi import APIRouter

from .kobetsu import router as kobetsu_router
from .auth import router as auth_router

api_router = APIRouter()

# Include routers
api_router.include_router(
    auth_router,
    prefix="/auth",
    tags=["Authentication"]
)

api_router.include_router(
    kobetsu_router,
    prefix="/kobetsu",
    tags=["Kobetsu Keiyakusho (個別契約書)"]
)
