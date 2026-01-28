from typing import Annotated

from pydantic import AfterValidator, EmailStr


def to_lowercase(v: EmailStr) -> EmailStr:
    return v.lower()


NormalizedEmail = Annotated[EmailStr, AfterValidator(to_lowercase)]
