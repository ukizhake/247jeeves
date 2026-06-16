from fastapi import APIRouter

from api.routes.compute import router as compute_router
from api.routes.health import router as health_router
from api.routes.import_ import router as import_router
from api.routes.profiles import router as profiles_router
from api.routes.rules import router as rules_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(compute_router)
api_router.include_router(import_router)
api_router.include_router(profiles_router)
api_router.include_router(rules_router)
