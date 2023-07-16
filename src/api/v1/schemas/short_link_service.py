from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, validator, Field

from api.v1.constants.contstants import ORIGINAL_URL_KEY, HTTP_CHECK, SHORT_URL


class GetShotLinkRequest(BaseModel):
    """Класс запроса на получение укороченной ссылки"""
    original_url: str = Field(alias=ORIGINAL_URL_KEY)

    @validator('original_url')
    def check_value(cls, original_url):
        if HTTP_CHECK not in original_url:
            raise ValueError('the value must be an http link')
        return original_url

    class Config:
        #  Позволяет возвращать alias, а в работе использовать "питонячее имя"
        allow_population_by_field_name = True


class ShortLinkBase(BaseModel):
    """Базовый класс укороченной ссылки"""

    short_id: str
    short_url: str


class ShotLinkResponse(ShortLinkBase):
    """Класс ответа на запрос на получения укороченной ссылки"""
    short_id: str = Field(alias=ORIGINAL_URL_KEY)
    short_url: str = Field(alias=SHORT_URL)

    class Config:
        #  Позволяет возвращать alias, а в работе использовать "питонячее имя"
        allow_population_by_field_name = True
        orm_mode = True


class GetShotLinksListRequest(BaseModel):
    """Класс запроса на получение укороченных ссылок пачками"""
    __root__: list[GetShotLinkRequest]


class ShortLinkCreate(BaseModel):
    """Класс создания укороченной ссылки"""
    original_link: str
    link_id: str
    short_link: str


class ShortLinkUpdate(BaseModel):
    """Класс обновления информации о ссылке"""
    usages_count: int


class ShortLinkUsageHistoryAdd(BaseModel):
    """Класс добавления информации об использовании ссылки"""

    short_link_id: UUID = Field(default_factory=uuid4)
    client_ip: str


class FullInfo(BaseModel):
    """Дополнительная детализированная информация о каждом переходе"""

    use_at: datetime
    client_ip: str

    class Config:
        orm_mode = True


class ShortUrlInfoResponse(BaseModel):
    """Класс ответ а запрос статуса использования URL."""

    click_count: int


class ShortUrlInfoResponseDetail(ShortUrlInfoResponse):
    """Класс ответ а запрос статуса использования URL с дополнительной информацией."""

    detail: list[FullInfo]


class DBConnStatusResponse(BaseModel):
    """Класс ответа на запрос доступности БД"""

    is_available: bool


class ShotLinksListCreate(BaseModel):
    """Класс для создания коротких ссылок пачками"""

    __root__: list[ShortLinkCreate]


class ShotLinksListResponse(BaseModel):
    """Класс ответа на запрос создания коротких ссылок пачками"""

    __root__: list[ShotLinkResponse]

    class Config:
        orm_mode = True
