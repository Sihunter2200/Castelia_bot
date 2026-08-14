import asyncio
import os
import re

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from database.db import async_session
from database.models import Material, MaterialVariant

IMAGES_DIR = 'data/images'

# служебные фото, которые не являются вариантами материалов
SERVICE_PHOTOS = {'castelia_start_photo.jpg', 'menu_group_1.jpg', 'menu_group_2.jpg', 'menu_group_3.jpg'}

# group -> путь к общему фото группы
GROUP_PHOTOS = {
    1: 'data/images/menu_group_1.jpg',
    2: 'data/images/menu_group_2.jpg',
    3: 'data/images/menu_group_3.jpg',
}

# (имя, группа) — порядок задаёт номер материала в имени файла (_1.._21)
MATERIALS = [
    ('Alluminium board', 1),
    ('Ancient wood', 1),
    ('Crood wood ripple board', 1),
    ('Line Sone', 1),
    ('Marble', 1),
    ('New Rock', 1),
    ('Polished Concrete', 1),
    ('Polished stone PRO', 2),
    ('Polywood', 2),
    ('Ripple Board', 2),
    ('Ripple board под покраску «выпуклый»', 2),
    ('Rockface Stone', 2),
    ('Roman pillar', 2),
    ('Rough surface', 2),
    ('Round line stone', 3),
    ('Rust board', 3),
    ('Sandstone Nile', 3),
    ('Slate', 3),
    ('Terrazo', 3),
    ('Travertine Italian', 3),
    ('Travertine PRO', 3),
]

_FILE_RE = re.compile(r'^(?P<name>.+)_(?P<num>\d+)\.(?P<ext>[a-zA-Z]+)$')


def collect_variants() -> dict[int, list[dict]]:
    """Сканирует data/images и группирует файлы по номеру материала."""
    variants: dict[int, list[dict]] = {}
    for filename in sorted(os.listdir(IMAGES_DIR)):
        if filename in SERVICE_PHOTOS:
            continue
        m = _FILE_RE.match(filename)
        if not m:
            print(f'Пропущен файл без номера материала: {filename}')
            continue
        num = int(m.group('num'))
        if not 1 <= num <= len(MATERIALS):
            print(f'Пропущен файл с несуществующим номером материала: {filename}')
            continue
        name_variant = m.group('name').strip()
        path = f'{IMAGES_DIR}/{filename}'
        variants.setdefault(num, []).append({'name_variant': name_variant, 'photo_path': path})
    return variants


async def seed_catalog():
    variants = collect_variants()
    async with async_session() as session:
        for idx, (name, group) in enumerate(MATERIALS, start=1):
            ins = pg_insert(Material)
            stmt = (
                ins
                .values(
                    name=name,
                    group=group,
                    menu_photo_path=GROUP_PHOTOS[group],
                )
                .on_conflict_do_update(
                    index_elements=[Material.name],
                    set_={
                        'group': ins.excluded.group,
                        'menu_photo_path': ins.excluded.menu_photo_path,
                    },
                )
            )
            await session.execute(stmt)

            material_result = await session.execute(
                select(Material).where(Material.name == name)
            )
            material = material_result.scalar_one()

            for variant in variants.get(idx, []):
                v_ins = pg_insert(MaterialVariant)
                v_stmt = (
                    v_ins
                    .values(
                        material_id=material.id,
                        name_variant=variant['name_variant'],
                        photo_path=variant['photo_path'],
                    )
                    .on_conflict_do_update(
                        index_elements=[MaterialVariant.material_id,
                                        MaterialVariant.name_variant],
                        set_={'photo_path': v_ins.excluded.photo_path},
                    )
                )
                await session.execute(v_stmt)

        await session.commit()
    total = sum(len(v) for v in variants.values())
    print(f'Загружено материалов: {len(MATERIALS)}')
    print(f'Загружено вариантов: {total}')


if __name__ == '__main__':
    asyncio.run(seed_catalog())