from database.db import Base

from sqlalchemy import BigInteger, String, ForeignKey, DateTime, func, Integer, Enum, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    username: Mapped[str | None] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class Material(Base):
    __tablename__ = 'materials'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True, nullable=False)
    group: Mapped[int] = mapped_column(default=1)
    menu_photo_path: Mapped[str | None] = mapped_column()
    color_photo_path: Mapped[str | None] = mapped_column()


class MaterialVariant(Base):
    __tablename__ = 'material_variants'
    __table_args__ = (
        UniqueConstraint('material_id', 'name_variant', name='uq_material_variant_name'),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    material_id: Mapped[int] = mapped_column(ForeignKey('materials.id'))
    name_variant: Mapped[str] = mapped_column()
    photo_path: Mapped[str] = mapped_column()


class Photo(Base):
    __tablename__ = 'photo_path'

    key: Mapped[str] = mapped_column(primary_key=True)
    path_photo: Mapped[str] = mapped_column()