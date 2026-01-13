from fastapi import APIRouter

from app.auth.dependencies import AuthServiceDep
from app.auth.dtos import AuthDTO
from app.auth.schemas import AuthCreate, AuthRead
from app.users.schemes import UserCreate

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=AuthRead)
async def login(auth_service: AuthServiceDep, auth_data: AuthCreate) -> AuthDTO:
    return await auth_service.login(auth_data)


@router.post("/register", response_model=AuthRead)
async def register_user(auth_service: AuthServiceDep, user_data: UserCreate) -> AuthDTO:
    return await auth_service.register(user_data)
