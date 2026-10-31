from collections.abc import Generator
from functools import lru_cache

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


@lru_cache
def get_engine():
    url = get_settings().database_url
    if not url:
        raise HTTPException(status_code=503, detail="Database is not configured. Set DATABASE_URL in backend/.env.")
    return create_engine(url, pool_pre_ping=True, pool_recycle=1800)


def get_db() -> Generator[Session, None, None]:
    engine = get_engine()
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with factory() as session:
        yield session
