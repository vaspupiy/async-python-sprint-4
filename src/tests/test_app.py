import pytest

# Импортируем сюда переменную приложения app, инициализированную в файле app.py
from fastapi import status


@pytest.mark.asyncio
async def test_get_db_connect_status(test_app):
    response = test_app.get('/api/v1/ping')
    # Проверяем, что запрос успешно обработан...
    assert response.status_code == 200
    assert response.json().get("is_available") is not None
    assert isinstance(response.json().get("is_available"), bool)


@pytest.mark.asyncio
async def test_get_short_link(test_app):
    response = test_app.post('/api/v1/', json={"original-url": "https://dzen.ru/"})
    assert response.status_code == status.HTTP_201_CREATED

