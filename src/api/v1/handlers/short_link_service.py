import logging
from logging import config as logging_config

from fastapi import Request, Query, status, HTTPException
from fastapi.responses import ORJSONResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import LEN_SHORT_LINK, LINK_NOT_FOUND, PAGE_DELETED, WAS_DELETED
from api.v1.schemas.short_link_service import (
    GetShotLinkRequest,
    GetShotLinksListRequest,
    ShotLinkResponse,
    ShortLinkCreate,
    ShortLinkUsageHistoryAdd,
    ShortLinkUpdate,
    ShortUrlInfoResponse,
    ShortUrlInfoResponseDetail,
    DBConnStatusResponse,
    ShotLinksListCreate,
    ShotLinksListResponse
)
from core.config import PROJECT_URL
from core.logger import LOGGING
from models.short_link import ShortLink, ShortLinkHistory
from services.base import RepositoryDB

logging_config.dictConfig(LOGGING)
logger = logging.getLogger(__name__)

sl_crud = RepositoryDB(ShortLink)
slh_crud = RepositoryDB(ShortLinkHistory)


def get_item_object_in_for_url(original_url: str, len_short_link: int) -> ShortLinkCreate:
    logger.info("start get_item_object_in_for_url; original_url: %s", original_url)
    link_id = sl_crud.create_short_url(len_short_link)
    logger.debug("link_id: %s", link_id)
    obj_in = ShortLinkCreate(
        original_link=original_url,
        link_id=link_id,
        short_link=f"{PROJECT_URL}{link_id}",
    )
    logger.info("end get_item_object_in_for_url; obj_in: %s", obj_in)
    return obj_in


async def get_short_link_handler(request: GetShotLinkRequest, db: AsyncSession):
    logger.info("start get_short_link_handler")
    obj_in = get_item_object_in_for_url(request.original_url, LEN_SHORT_LINK)
    short_link_obj = await sl_crud.create(db=db, obj_in=obj_in)
    logger.debug("short_link: %s", short_link_obj)
    resp = ShotLinkResponse(short_id=short_link_obj.link_id, short_url=short_link_obj.short_link).dict(by_alias=True)
    logger.info("end get_short_link_handler: %s", resp)
    return ORJSONResponse(
        resp,
        status_code=status.HTTP_201_CREATED
    )


async def batch_upload_links_handler(request: GetShotLinksListRequest, db: AsyncSession):
    logger.info("start batch_upload_links_handler: request: %s", request.__root__)
    list_obj = [get_item_object_in_for_url(item.original_url, LEN_SHORT_LINK) for item in request.__root__]
    logger.debug("list_obj: %s", list_obj)
    objects_in = ShotLinksListCreate(
        __root__=list_obj
    )
    logger.debug("objects_in: %s", objects_in)
    multi_obj = await sl_crud.update_multi(db=db, objects_in=objects_in)
    logger.debug("multi_obj: %s; type(multi_obj): %s", multi_obj, type(multi_obj))
    list_resp = [ShotLinkResponse(short_id=obj.link_id, short_url=obj.short_link) for obj in multi_obj]
    resp = ShotLinksListResponse(
        __root__=list_resp
    ).dict(by_alias=True)

    logger.info("end batch_upload_links_handler: request: %s", resp)
    return ORJSONResponse(
        resp["__root__"],
        status_code=status.HTTP_201_CREATED
    )


async def get_db_connect_status_handler(db: AsyncSession):
    logger.info("start get_db_connect_status_handler")
    ping_result: bool = await sl_crud.ping_db(db)
    resp = DBConnStatusResponse(is_available=ping_result).dict()
    logger.info("end get_db_connect_status_handler: resp: %s", resp)
    return ORJSONResponse(resp, status_code=status.HTTP_200_OK)


async def delete_short_url_handler(shorten_url_id: str, db):
    logger.info("start delete_short_url_handler, shorten_url_id: %s", shorten_url_id)
    sl_obj = await sl_crud.get_for_shorten_url(db=db, shorten_url_id=shorten_url_id)
    logger.debug("sl_obj.id: %s", sl_obj.id)
    if not sl_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=LINK_NOT_FOUND)
    if not sl_obj.is_active:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail=PAGE_DELETED)
    sl_del_obj = await sl_crud.delete(db=db, db_obj=sl_obj)
    logger.debug("sl_del_obj.is_active %s", sl_del_obj.is_active)
    logger.info("end delete_short_url_handler, shorten_url_id: %s", shorten_url_id)
    return ORJSONResponse({shorten_url_id: WAS_DELETED}, status_code=status.HTTP_200_OK)


async def redirect_for_short_url_id_handler(shorten_url_id: str, request: Request, db: AsyncSession):
    logger.info("start redirect_for_short_url_id_handler, shorten_url_id: %s", shorten_url_id)
    client_info = f"{request.client.host}:{request.client.port}"
    logger.debug("client_info: %s", client_info)
    sl_obj = await sl_crud.get_for_shorten_url(db, shorten_url_id)
    if not sl_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=LINK_NOT_FOUND)
    if not sl_obj.is_active:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail=PAGE_DELETED)
    slh_create_obj = ShortLinkUsageHistoryAdd(
        short_link_id=sl_obj.id,
        client_ip=client_info,
    )
    logger.debug("sl_obj: %s; sl_obj.id_type: %s", sl_obj, type(sl_obj.id))
    slh_obj = await slh_crud.create(db=db, obj_in=slh_create_obj)
    logger.debug("slh_obj: %s", slh_obj)
    usage_up = ShortLinkUpdate(usages_count=sl_obj.usages_count + 1)
    logger.debug("usage_up: %s; type(usage_up): %s", usage_up, type(usage_up))
    sl_obj_up = await sl_crud.update(db=db, db_obj=sl_obj, obj_in=usage_up)
    logger.debug("sl_obj_up: %s; sl_obj_up.id_type: %s", sl_obj_up, type(sl_obj_up.id))
    logger.info("end redirect_for_short_url_id_handler; sl_obj.original_link:%s", sl_obj.original_link)
    return RedirectResponse(sl_obj.original_link, status_code=status.HTTP_307_TEMPORARY_REDIRECT)


async def get_short_url_info_handler(
        shorten_url_id: str,
        db: AsyncSession,
        full_info: bool = Query(default=False, alias="full-info"),
        max_result: int = Query(default=10, alias="max-result"),
        offset: int = Query(default=0, ),
):
    logger.info("start get_short_url_info_handler")
    sl_obj = await sl_crud.get_for_shorten_url(db, shorten_url_id)
    if not sl_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=LINK_NOT_FOUND)
    status_info = ShortUrlInfoResponse(click_count=sl_obj.usages_count).dict()
    logger.debug("status_info: %s", status_info)
    if not full_info:
        logger.info("end get_short_url_info_handler; not detail")
        return ORJSONResponse(
            status_info,
            status_code=status.HTTP_200_OK)

    detail = await slh_crud.get_detail_history(db=db, link_id=sl_obj.id, limit=max_result, offset=offset)
    logger.debug("len(detail): %s", len(detail))
    detail_resp = ShortUrlInfoResponseDetail(
        click_count=sl_obj.usages_count,
        detail=detail
    ).dict()
    logger.debug("detail_resp: %s", detail_resp)
    return ORJSONResponse(
        detail_resp,
        status_code=status.HTTP_200_OK)
