from fastapi import APIRouter
from .search._routes import router as search_router


router = APIRouter(
    prefix = "/api")

router.include_router(
    router = search_router)