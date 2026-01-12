from fastapi import APIRouter, FastAPI

from app.auth.router import router as auth_router
from app.core.exception_handlers import register_exceptions_handler
from app.core.lifespan import lifespan
from app.core.logging import setup_logging
from app.users.router import router as users_router

setup_logging()


app = FastAPI(title="Cloud storage API", lifespan=lifespan)
register_exceptions_handler(app)

api_router = APIRouter()

api_router.include_router(users_router)
api_router.include_router(auth_router)

app.include_router(api_router, prefix="/api/v1")
