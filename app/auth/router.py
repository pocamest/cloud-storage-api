from fastapi import APIRouter, status

from app.auth.dependencies import AuthServiceDep
from app.auth.dtos import AuthDTO, TokenDTO
from app.auth.schemas import LoginRequest, LoginResponse, RefreshRequest, TokenResponse
from app.users.schemas import UserCreate

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login(auth_service: AuthServiceDep, auth_data: LoginRequest) -> AuthDTO:
    return await auth_service.login(auth_data)


@router.post(
    "/register", response_model=LoginResponse, status_code=status.HTTP_201_CREATED
)
async def register(auth_service: AuthServiceDep, user_data: UserCreate) -> AuthDTO:
    return await auth_service.register(user_data)


@router.post("/refresh", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def refresh(
    auth_service: AuthServiceDep, refresh_data: RefreshRequest
) -> TokenDTO:
    return await auth_service.refresh(refresh_data.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(auth_service: AuthServiceDep, refresh_data: RefreshRequest) -> None:
    await auth_service.logout(refresh_data.refresh_token)
