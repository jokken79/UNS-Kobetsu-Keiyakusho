"""
API v1 Router
Aggregates all API endpoints under versioned prefix.
"""
from fastapi import APIRouter

from .kobetsu import router as kobetsu_router
from .auth import router as auth_router
from .factories import router as factories_router
from .employees import router as employees_router

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

api_router.include_router(
    factories_router,
    prefix="/factories",
    tags=["Factories (派遣先/工場)"]
)

api_router.include_router(
    employees_router,
    prefix="/employees",
    tags=["Employees (派遣社員)"]
)
