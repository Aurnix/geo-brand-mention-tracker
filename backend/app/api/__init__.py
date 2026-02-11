from fastapi import APIRouter

from app.api.auth import router as auth_router
from app.api.brands import router as brands_router
from app.api.competitors import router as competitors_router
from app.api.queries import router as queries_router
from app.api.results import router as results_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(brands_router)
api_router.include_router(competitors_router)
api_router.include_router(queries_router)
api_router.include_router(results_router)
