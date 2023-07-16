from fastapi import APIRouter, Request, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from api.v1.handlers.short_link_service import (
    get_short_link_handler,
    redirect_for_short_url_id_handler,
    get_short_url_info_handler,
    get_db_connect_status_handler,
    delete_short_url_handler,
    batch_upload_links_handler,
)
from api.v1.schemas.short_link_service import (
    GetShotLinkRequest,
    GetShotLinksListRequest,
    ShotLinkResponse,
    ShortUrlInfoResponse,
    ShortUrlInfoResponseDetail,
    DBConnStatusResponse,
    ShotLinksListResponse
)
# Объект router, в котором регистрируем обработчики
from db.short_links_db_base import get_session

router = APIRouter()


@router.post("/", response_model=ShotLinkResponse, status_code=status.HTTP_201_CREATED)
async def get_short_link(request: GetShotLinkRequest, db: AsyncSession = Depends(get_session), ):
    return await get_short_link_handler(request=request, db=db)


@router.post("/batch-upload", response_model=ShotLinksListResponse, status_code=status.HTTP_201_CREATED)
async def batch_upload_links(request: GetShotLinksListRequest, db: AsyncSession = Depends(get_session), ):
    return await batch_upload_links_handler(request, db)


@router.get("/ping", response_model=DBConnStatusResponse, status_code=status.HTTP_200_OK)
async def get_db_connect_status(db: AsyncSession = Depends(get_session), ):
    return await get_db_connect_status_handler(db)


@router.get("/{shorten_url_id}", status_code=status.HTTP_307_TEMPORARY_REDIRECT)
async def redirect_for_short_url_id(shorten_url_id: str, request: Request, db: AsyncSession = Depends(get_session), ):
    return await redirect_for_short_url_id_handler(shorten_url_id, request, db)


@router.delete("/{shorten_url_id}")
async def delete_short_url(shorten_url_id: str, db: AsyncSession = Depends(get_session), ):
    return await delete_short_url_handler(shorten_url_id, db)


@router.get("/{shorten_url_id}/status",
            response_model=ShortUrlInfoResponse | ShortUrlInfoResponseDetail,
            status_code=status.HTTP_200_OK)
async def get_short_url_info(
        shorten_url_id: str,
        full_info: bool = Query(default=False, alias="full-info"),
        max_result: int = Query(default=10, alias="max-result"),
        offset: int = Query(default=0, ),
        db: AsyncSession = Depends(get_session),
):
    return await get_short_url_info_handler(
        shorten_url_id,
        full_info=full_info,
        max_result=max_result,
        offset=offset,
        db=db,
    )
