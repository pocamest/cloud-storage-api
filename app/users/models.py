import uuid

from sqlalchemy import UUID, CheckConstraint, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.users.constants import UQ_USERS_EMAIL


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        # TODO: привести названия ограничений/чеков во всех моделях
        # к единому виду согласно соглашению об именовании
        UniqueConstraint("email", name=UQ_USERS_EMAIL),
        CheckConstraint("email = LOWER(email)", name="email_lowercase_check"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    def __repr__(self) -> str:
        return f"<User(id={self.id!r}, email={self.email!r})>"
