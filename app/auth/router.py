from fastapi import APIRouter, status

from app.auth.dependencies import AuthServiceDep
from app.auth.dtos import AuthDTO, TokenDTO
from app.auth.schemas import AuthCreate, AuthRead, AuthRefresh, TokenRead
from app.users.schemas import UserCreate

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=AuthRead, status_code=status.HTTP_200_OK)
async def login(auth_service: AuthServiceDep, auth_data: AuthCreate) -> AuthDTO:
    return await auth_service.login(auth_data)


@router.post("/register", response_model=AuthRead, status_code=status.HTTP_201_CREATED)
async def register(auth_service: AuthServiceDep, user_data: UserCreate) -> AuthDTO:
    return await auth_service.register(user_data)


@router.post("/refresh", response_model=TokenRead, status_code=status.HTTP_200_OK)
async def refresh(auth_service: AuthServiceDep, refresh_data: AuthRefresh) -> TokenDTO:
    return await auth_service.refresh(refresh_data.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(auth_service: AuthServiceDep, refresh_data: AuthRefresh) -> None:
    await auth_service.logout(refresh_data.refresh_token)
