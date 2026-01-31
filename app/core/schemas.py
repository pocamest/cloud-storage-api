from pydantic import BaseModel, ConfigDict, Field

from app.core.exceptions import ErrorCode


class ErrorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    detail: str
    code: ErrorCode = Field(validation_alias="error_code")
