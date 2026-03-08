import uuid

from sqlalchemy import (
    UUID,
    BigInteger,
    CheckConstraint,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.storage.types import StorageItemKind

UNIQUE_NAME_WITHIN_PARENT = "unique_name_within_parent"


class StorageItem(Base):
    __tablename__ = "storage_items"
    __table_args__ = (
        UniqueConstraint(
            "name",
            "owner_id",
            "parent_id",
            name=UNIQUE_NAME_WITHIN_PARENT,
            postgresql_nulls_not_distinct=True,
        ),
        CheckConstraint(
            "kind != 'file' OR size IS NOT NULL", name="check_size_not_null_for_file"
        ),
        CheckConstraint(
            "kind != 'file' OR s3_key IS NOT NULL",
            name="check_s3_key_not_null_for_file",
        ),
        CheckConstraint("parent_id != id", name="check_parent_is_not_self"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    kind: Mapped[str] = mapped_column(String(20))

    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
    # parent_id = None/NULL считается корневой папкой у пользователя
    parent_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("storage_items.id", ondelete="CASCADE"), nullable=True, index=True
    )

    __mapper_args__ = {
        "polymorphic_on": kind,
        "polymorphic_identity": "storage_item",
        # сразу загружает поля наследников, потому что lazy_load в async не работает
        "with_polymorphic": "*",
    }

    def __repr__(self) -> str:
        return (
            f"<StorageItem("
            f"id={self.id!r}, kind={self.kind!r}, "
            f"name={self.name!r}, parent_id={self.parent_id!r})>"
        )


class File(StorageItem):
    size: Mapped[int] = mapped_column(BigInteger, nullable=True)
    s3_key: Mapped[str] = mapped_column(String(255), nullable=True, unique=True)

    __mapper_args__ = {"polymorphic_identity": StorageItemKind.FILE}


class Folder(StorageItem):
    __mapper_args__ = {"polymorphic_identity": StorageItemKind.FOLDER}
