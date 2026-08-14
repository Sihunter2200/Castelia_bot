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


async def add_lead(session: AsyncSession, telegram_id: int, username: str | None,
                   material_name: str | None, color_name: str | None,
                   result_path: str | None = None, result_url: str | None = None,
                   user_photo_path: str | None = None):
    lead = models.Lead(
        telegram_id=telegram_id,
        username=username,
        material_name=material_name,
        color_name=color_name,
        result_path=result_path,
        result_url=result_url,
        user_photo_path=user_photo_path,
    )
    session.add(lead)
    await session.commit()
    await session.refresh(lead)
    return lead


async def get_last_lead(session: AsyncSession, telegram_id: int) -> models.Lead | None:
    stmt = (
        select(models.Lead)
        .where(models.Lead.telegram_id == telegram_id)
        .order_by(models.Lead.created_at.desc(), models.Lead.id.desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar()


async def set_lead_result(session: AsyncSession, telegram_id: int, result_path: str | None, result_url: str | None):
    lead = await get_last_lead(session, telegram_id)
    if lead is None:
        return
    lead.result_path = result_path
    lead.result_url = result_url
    await session.commit()
