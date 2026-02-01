from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from common.repositories.cross_tenant.user_repository import UserRepository
from management_api.dependencies import get_db_session
from management_api.schemas.users import UserCreate, UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserResponse, status_code=201)
async def create_user(body: UserCreate, session: AsyncSession = Depends(get_db_session)):
    repo = UserRepository(session)
    user = await repo.add(email=body.email)
    await session.commit()
    return user


@router.get("", response_model=List[UserResponse])
async def list_users(limit: int = 100, offset: int = 0, session: AsyncSession = Depends(get_db_session)):
    repo = UserRepository(session)
    return await repo.get_all(limit=limit, offset=offset)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: UUID, session: AsyncSession = Depends(get_db_session)):
    repo = UserRepository(session)
    return await repo.get_by_id(user_id)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(user_id: UUID, body: UserUpdate, session: AsyncSession = Depends(get_db_session)):
    repo = UserRepository(session)
    user = await repo.get_by_id(user_id)
    if body.email is not None:
        user.email = body.email
    user = await repo.update(user)
    await session.commit()
    return user


@router.delete("/{user_id}", status_code=204)
async def delete_user(user_id: UUID, session: AsyncSession = Depends(get_db_session)):
    repo = UserRepository(session)
    await repo.deactivate(user_id)
    await session.commit()
