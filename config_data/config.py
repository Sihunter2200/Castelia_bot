from dataclasses import dataclass
from environs import Env

@dataclass
class Tg_bot:
    token: str
    superadmin: list[int]


@dataclass
class DbConfig:
    dsn: str
    is_echo: bool


@dataclass
class Config:
    tg_bot: Tg_bot
    db: DbConfig
    proxy: str | None
    gptunnel_api_key: str
    imgbb_api_key: str | None
    upload_proxy: str | None

def load_config(path: str | None = None) -> Config:
    env = Env()
    env.read_env(path)

    return Config(
        tg_bot=Tg_bot(
            token=env('BOT_TOKEN'),
            superadmin=[int(admin_id) for admin_id in env.list('ADMINS')],
        ),
        db=DbConfig(
            # asyncpg для асинхронной работы
            dsn=(
                f"postgresql+asyncpg://{env('DB_USER')}:{env('DB_PASSWORD')}"
                f"@{env('DB_HOST')}:{env('DB_PORT')}/{env('DB_NAME')}"
            ),
            is_echo=env.bool('DB_IS_ECHO'),
        ),
        proxy=env('PROXY', default=None),
        gptunnel_api_key=env('GPTUNNEL_API_KEY'),
        imgbb_api_key=env('IMGBB_API_KEY', default=None),
        upload_proxy=env('UPLOAD_PROXY', default=None),
    )