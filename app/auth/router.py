from fastapi import APIRouter

from app.auth.dependencies import AuthServiceDep
from app.auth.dtos import AuthDTO, TokenDTO
from app.auth.schemas import AuthCreate, AuthRead, AuthRefresh, TokenRead
from app.users.schemas import UserCreate

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=AuthRead)
async def login(auth_service: AuthServiceDep, auth_data: AuthCreate) -> AuthDTO:
    return await auth_service.login(auth_data)


@router.post("/register", response_model=AuthRead)
async def register(auth_service: AuthServiceDep, user_data: UserCreate) -> AuthDTO:
    return await auth_service.register(user_data)


@router.post("/refresh", response_model=TokenRead)
async def refresh(auth_service: AuthServiceDep, refresh_data: AuthRefresh) -> TokenDTO:
    return await auth_service.refresh(refresh_data.refresh_token)
