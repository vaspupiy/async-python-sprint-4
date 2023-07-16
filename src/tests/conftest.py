import pytest_asyncio
from starlette.testclient import TestClient

import asyncio

import pytest

from main import app


@pytest_asyncio.fixture
def test_app():
    client = TestClient(app)
    yield client


@pytest.yield_fixture(scope='session')
def event_loop(request):
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
