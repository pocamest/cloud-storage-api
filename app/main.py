from fastapi import APIRouter, FastAPI

from app.core.exception_handlers import register_exceptions_handler
from app.core.logging import setup_logging
from app.users.router import router as users_router

setup_logging()

app = FastAPI(title="Cloud storage API")
register_exceptions_handler(app)

api_router = APIRouter()

api_router.include_router(users_router)

app.include_router(api_router, prefix="/api/v1")
