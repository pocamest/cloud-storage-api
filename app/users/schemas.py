import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.core.types import NormalizedEmail


class UserCreate(BaseModel):
    email: NormalizedEmail
    password: str = Field(min_length=8, max_length=64)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
