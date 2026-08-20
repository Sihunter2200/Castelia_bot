import aiohttp
import asyncio
import base64
import json
import logging
import os

from config_data.config import load_config


logger = logging.getLogger(__name__)

_config = load_config()
API_HEADERS = {'Authorization': _config.gptunnel_api_key}


async def upload_imgbb(path: str, session: aiohttp.ClientSession, proxy: str | None = None) -> str:
    if not _config.imgbb_api_key:
        raise aiohttp.ClientError('imgbb: ключ не задан в .env')
    with open(path, 'rb') as f:
        b64 = base64.b64encode(f.read()).decode('utf-8')
    form = aiohttp.FormData()
    form.add_field('image', b64)
    async with session.post(
        f'https://api.imgbb.com/1/upload?key={_config.imgbb_api_key}',
        data=form,
        proxy=proxy,
        timeout=aiohttp.ClientTimeout(total=120),
    ) as resp:
        d = await resp.json()
    if resp.status != 200 or not d.get('success') or not d.get('data', {}).get('url'):
        raise aiohttp.ClientError(f'imgbb status {resp.status}: {d}')
    return d['data']['url']


async def upload_catbox(path: str, session: aiohttp.ClientSession) -> str:
    form = aiohttp.FormData()
    with open(path, 'rb') as f:
        form.add_field('reqtype', 'fileupload')
        form.add_field('fileToUpload', f, filename=os.path.basename(path))
        async with session.post(
            'https://catbox.moe/user/api.php',
            data=form,
            timeout=aiohttp.ClientTimeout(total=120)
        ) as resp:
            text = (await resp.text()).strip()
            logger.info('catbox upload %s: status=%s ответ=%s', path, resp.status, text[:200])
            if resp.status != 200 or not text.startswith('https://'):
                raise aiohttp.ClientError(f'catbox status {resp.status}: {text[:200]}')
    return text


async def upload_tmpfiles(path: str, session: aiohttp.ClientSession) -> str:
    form = aiohttp.FormData()
    with open(path, 'rb') as f:
        form.add_field('file', f, filename=os.path.basename(path))
        async with session.post(
            'https://tmpfiles.org/api/v1/upload',
            data=form,
            timeout=aiohttp.ClientTimeout(total=120)
        ) as resp:
            data = await resp.json()
    if resp.status != 200 or data.get('status') != 'success':
        raise aiohttp.ClientError(f'tmpfiles status {resp.status}: {data}')
    url = data['data']['url']
    return url.replace('tmpfiles.org/', 'tmpfiles.org/dl/')


async def upload_graph(path: str, session: aiohttp.ClientSession) -> str:
    form = aiohttp.FormData()
    with open(path, 'rb') as f:
        form.add_field('file', f, filename=os.path.basename(path))
        async with session.post(
            'https://graph.org/upload',
            data=form,
            timeout=aiohttp.ClientTimeout(total=120)
        ) as resp:
            data = await resp.json()
    if resp.status != 200 or not isinstance(data, list) or not data:
        raise aiohttp.ClientError(f'graph status {resp.status}: {data}')
    return 'https://graph.org' + data[0]['src']


UPLOADERS = [
    ('imgbb', upload_imgbb, True),
    ('catbox', upload_catbox, False),
    ('tmpfiles', upload_tmpfiles, False),
    ('graph', upload_graph, False),
]


async def upload_to_hosting(path: str, session: aiohttp.ClientSession, proxy: str | None = None) -> str:
    last_error = None
    for host, uploader, use_proxy in UPLOADERS:
        try:
            url = await uploader(path, session, proxy=proxy if use_proxy else None)
            logger.info('upload OK via %s: %s -> %s', host, path, url)
            return url
        except Exception as e:
            last_error = f'{host}: {e}'
            logger.info('upload %s failed via %s: %s', path, host, e)
    raise aiohttp.ClientError(f'все хостинги недоступны: {last_error}')


async def visualize(room_path: str, material_path: str, size_tile: str, photo_layout: str, layout_prompt: str):
    async with aiohttp.ClientSession() as session:
        results = await asyncio.gather(
            upload_to_hosting(room_path, session, _config.upload_proxy),
            upload_to_hosting(material_path, session, _config.upload_proxy),
            upload_to_hosting(photo_layout, session, _config.upload_proxy),
            return_exceptions=True
        )

        url_room, url_material, url_layout = results[0], results[1], results[2]

        if isinstance(url_room, Exception) or isinstance(url_material, Exception) or isinstance(url_layout, Exception):
            return (None, 'upload_failed')

        body = {
            "model": "nano-banana-2",
            "prompt": f"The first image is a photo of a room. Replace the wall covering in the first image with exactly the material shown in the second image, using tiles of size {size_tile} mm. Arrange the tiles according to the {layout_prompt} layout shown in the third image. Keep the room's lighting, shadows, perspective and furniture. Make the material look realistic and seamless.",
            "inputs": {"image_input": [url_room, url_material, url_layout]},
            "params": {"aspect_ratio": "1:1"},
            "wait": False
        }

        resp = await session.post(
            url='https://gptunnel.ru/api/v2/media/tasks',
            headers=API_HEADERS,
            json=body,
            timeout=aiohttp.ClientTimeout(total=60))
        text = await resp.text()
        logger.info('gptunnel POST: status=%s url_room=%s url_material=%s', resp.status, url_room, url_material)
        logger.info('gptunnel POST тело: %s', text[:500])
        if resp.status != 200:
            return (None, 'api_error')
        data = json.loads(text) if text else {}
        task_id = data['id']

        result = await wait_for_task(session, task_id)

        if result is None or result['status'] == 'failed':
            return (None, 'visualization_failed')
        if not result['result']:
            return (None, 'visualization_failed')
        return (result['result'][0]['url'], None)

async def get_task(session: aiohttp.ClientSession, task_id: str) -> dict:
    async with session.get(
        f'https://gptunnel.ru/api/v2/media/tasks/{task_id}',
        headers=API_HEADERS,
        timeout=aiohttp.ClientTimeout(total=60)
    ) as resp:
        return await resp.json()


async def wait_for_task(session, task_id, attempts=50, delay=5):
    last_status = None
    for i in range(attempts):
        task = await get_task(session, task_id)
        status = task.get('status')
        if status != last_status:
            logger.info('Статус задачи %s: %s', task_id, status)
            last_status = status
        if status in ('done', 'failed'):
            return task
        await asyncio.sleep(delay)
    logger.info('Ожидание задачи %s истекло (%s сек), последний статус: %s',
                task_id, attempts * delay, last_status)
    return None
