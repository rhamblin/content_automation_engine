from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from common.repositories.cross_tenant.channel_repository import ChannelRepository
from management_api.dependencies import get_db_session
from management_api.schemas.channels import ChannelCreate, ChannelResponse, ChannelUpdate

router = APIRouter(prefix="/channels", tags=["channels"])


@router.post("", response_model=ChannelResponse, status_code=201)
async def create_channel(body: ChannelCreate, session: AsyncSession = Depends(get_db_session)):
    repo = ChannelRepository(session)
    channel = await repo.add(identifier=body.identifier)
    await session.commit()
    return channel


@router.get("", response_model=List[ChannelResponse])
async def list_channels(limit: int = 100, offset: int = 0, session: AsyncSession = Depends(get_db_session)):
    repo = ChannelRepository(session)
    return await repo.get_all(limit=limit, offset=offset)


@router.get("/{channel_id}", response_model=ChannelResponse)
async def get_channel(channel_id: UUID, session: AsyncSession = Depends(get_db_session)):
    repo = ChannelRepository(session)
    return await repo.get_by_id(channel_id)


@router.patch("/{channel_id}", response_model=ChannelResponse)
async def update_channel(channel_id: UUID, body: ChannelUpdate, session: AsyncSession = Depends(get_db_session)):
    repo = ChannelRepository(session)
    channel = await repo.get_by_id(channel_id)
    if body.identifier is not None:
        channel.identifier = body.identifier
    channel = await repo.update(channel)
    await session.commit()
    return channel


@router.delete("/{channel_id}", status_code=204)
async def delete_channel(channel_id: UUID, session: AsyncSession = Depends(get_db_session)):
    repo = ChannelRepository(session)
    await repo.delete(channel_id)
    await session.commit()
