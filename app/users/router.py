from fastapi import APIRouter

from app.users.dependencies import UserServiceDep
from app.users.models import User
from app.users.schemes import UserCreate, UserRead

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserRead, status_code=201)
async def create_user(user_service: UserServiceDep, user_data: UserCreate) -> User:
    user = await user_service.create_user(user_data)
    return user
