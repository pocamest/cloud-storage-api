from fastapi import APIRouter

from app.auth.dependencies import AuthServiceDep
from app.auth.dtos import AuthDTO
from app.auth.schemas import AuthCreate, AuthRead

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=AuthRead)
async def login(auth_service: AuthServiceDep, auth_data: AuthCreate) -> AuthDTO:
    return await auth_service.login(auth_data=auth_data)
