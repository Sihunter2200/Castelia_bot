from sqlalchemy import delete, select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert
from aiogram_dialog import DialogManager

from database import models


async def add_user(session: AsyncSession, telegram_id: int, username: str | None):
    stmt = (
        pg_insert(models.User)
        .values(telegram_id=telegram_id, username=username)
        .on_conflict_do_update(
            index_elements=[models.User.telegram_id],
            set_={'username': username}
        )
    )


#async def get_names_materials(session: AsyncSession):
#    stmt = select(models.Material)
#    result = await session.execute(stmt)

#   return result.scalars().all()

async def get_material_by_group(session: AsyncSession, group: int):
    stmt = select(models.Material).where(models.Material.group == group)

    result = await session.execute(stmt)

    return result.scalars().all()


async def get_photo_by_group(session: AsyncSession, group: int):
    stmt = select(models.Material.menu_photo_path).where(models.Material.group == group)
    result = await session.execute(stmt)

    photo=result.first()
    return photo[0] if photo else None


async def get_name_by_id_material(session: AsyncSession, material_id: int):
    stmt = select(models.MaterialVariant.name_variant, models.MaterialVariant.id).where(models.MaterialVariant.material_id == material_id)

    result = await session.execute(stmt)

    return [{'id': row.id, 'name': row.name_variant} for row in result]


async def get_path_color_by_material_id(session: AsyncSession, material_id):
    stmt = select(models.Material.color_photo_path).where(models.Material.id == material_id)

    result = await session.execute(stmt)

    return result.scalar()


async def get_photo_by_color_id(session: AsyncSession, color_id: int):
    stmt = select(models.MaterialVariant.photo_path).where(models.MaterialVariant.id == color_id)

    result = await session.execute(stmt)

    return result.scalar()


async def get_material_and_variant_names(session: AsyncSession, color_id: int):
    stmt = (
        select(models.Material.name, models.MaterialVariant.name_variant)
        .join(models.MaterialVariant, models.MaterialVariant.material_id == models.Material.id)
        .where(models.MaterialVariant.id == color_id)
    )

    result = await session.execute(stmt)

    return result.first()