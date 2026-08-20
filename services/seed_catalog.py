import asyncio
import os
import re

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from database.db import async_session
from database.models import Material, MaterialVariant

IMAGES_DIR = 'data/images'

# служебные фото, которые не являются вариантами материалов
SERVICE_PHOTOS = {'castelia_start_photo.jpg', 'menu_group_1.jpeg', 'menu_group_2.jpeg', 'menu_group_3.jpeg'}

# group -> путь к общему фото группы
GROUP_PHOTOS = {
    1: 'data/images/menu_group_1.jpeg',
    2: 'data/images/menu_group_2.jpeg',
    3: 'data/images/menu_group_3.jpeg',
}

# (имя, группа) — порядок задаёт только порядок показа в меню,
# номер материала в имени файла берётся из MATERIAL_FILE_NUMS
MATERIALS = [
    ('Travertine Italian', 1),
    ('Travertine PRO', 1),
    ('Polished stone PRO', 1),
    ('Marble', 1),
    ('Polished Concrete', 1),
    ('Slate', 1),
    ('Round line stone', 1),
    ('Roman pillar', 2),
    ('Ripple Board', 2),
    ('Ripple board под покраску «выпуклый»', 2),
    ('Rough surface', 2),
    ('Polywood', 2),
    ('Terrazo', 2),
    ('Line Stone', 2),
    ('New Rock', 3),
    ('Alluminium board', 3),
    ('Ancient wood', 3),
    ('Crood wood ripple board', 3),
    ('Rockface Stone', 3),
    ('Rust board', 3),
    ('Sandstone Nile', 3),
]

# материал -> номер в имени файла (_1.._21); не зависит от порядка в MATERIALS
MATERIAL_FILE_NUMS = {
    'Alluminium board': 1,
    'Ancient wood': 2,
    'Crood wood ripple board': 3,
    'Line Stone': 4,
    'Marble': 5,
    'New Rock': 6,
    'Polished Concrete': 7,
    'Polished stone PRO': 8,
    'Polywood': 9,
    'Ripple Board': 10,
    'Ripple board под покраску «выпуклый»': 11,
    'Rockface Stone': 12,
    'Roman pillar': 13,
    'Rough surface': 14,
    'Round line stone': 15,
    'Rust board': 16,
    'Sandstone Nile': 17,
    'Slate': 18,
    'Terrazo': 19,
    'Travertine Italian': 20,
    'Travertine PRO': 21,
}

_FILE_RE = re.compile(r'^(?P<name>.+)_(?P<num>\d+)\.(?P<ext>[a-zA-Z]+)$')

# служебные файлы, которые не являются вариантами материалов
_SKIP_PREFIXES = ('color_grid_', 'material_color_', 'layout_photo_', 'menu_layout_')


def collect_variants() -> dict[int, list[dict]]:
    """Сканирует data/images и группирует файлы по номеру материала."""
    variants: dict[int, list[dict]] = {}
    for filename in sorted(os.listdir(IMAGES_DIR)):
        full = os.path.join(IMAGES_DIR, filename)
        if not os.path.isfile(full):
            continue
        if filename in SERVICE_PHOTOS or filename.startswith(_SKIP_PREFIXES):
            continue
        m = _FILE_RE.match(filename)
        if not m:
            print(f'Пропущен файл без номера материала: {filename}')
            continue
        num = int(m.group('num'))
        if num not in MATERIAL_FILE_NUMS.values():
            print(f'Пропущен файл с неизвестным номером материала: {filename}')
            continue
        name_variant = m.group('name').strip()
        path = f'{IMAGES_DIR}/{filename}'
        variants.setdefault(num, []).append({'name_variant': name_variant, 'photo_path': path})
    return variants


async def seed_catalog():
    variants = collect_variants()
    async with async_session() as session:
        for name, group in MATERIALS:
            num = MATERIAL_FILE_NUMS[name]
            color_path = f'{IMAGES_DIR}/material_color_{num}.jpg'
            if not os.path.exists(color_path):
                color_path = None
            ins = pg_insert(Material)
            stmt = (
                ins
                .values(
                    name=name,
                    group=group,
                    menu_photo_path=GROUP_PHOTOS[group],
                    color_photo_path=color_path
                )
                .on_conflict_do_update(
                    index_elements=[Material.name],
                    set_={
                        'group': ins.excluded.group,
                        'menu_photo_path': ins.excluded.menu_photo_path,
                        'color_photo_path': ins.excluded.color_photo_path
                    },
                )
            )
            await session.execute(stmt)

            material_result = await session.execute(
                select(Material).where(Material.name == name)
            )
            material = material_result.scalar_one()

            for variant in variants.get(num, []):
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