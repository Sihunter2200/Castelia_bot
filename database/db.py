from config_data.config import load_config

from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine


class Base(AsyncAttrs, DeclarativeBase):
    pass

config = load_config()

engine = create_async_engine(
    config.db.dsn,
    echo=config.db.is_echo
)

async_session = async_sessionmaker(engine, expire_on_commit=False)

