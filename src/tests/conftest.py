import os

import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from starlette.testclient import TestClient

import asyncio

import pytest

from db.short_links_db_base import get_session
from main import app

database_dsn_test = "postgresql+asyncpg://ypuser:yppass@localhost:5432/short_links_test"

Base = declarative_base()

engine_test = create_async_engine(database_dsn_test, echo=True, future=True)
async_session_test = sessionmaker(
    engine_test, class_=AsyncSession, expire_on_commit=False
)


async def override_get_session() -> AsyncSession:
    async with async_session_test() as session:
        yield session


@pytest_asyncio.fixture(scope="session")
def test_app():
    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as client:
        yield client
