from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from deps import get_db, get_current_user_id
from models.user import User

router = APIRouter()


class UpdateProfileBody(BaseModel):
    nickname: str | None = None
    avatar_url: str | None = None
    child_name: str | None = None
    child_grade: str | None = None
    serverchan_key: str | None = None


@router.get("/profile")
async def get_profile(
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """获取用户信息"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    return {
        "code": 0,
        "data": {
            "id": user.id,
            "nickname": user.nickname,
            "avatar_url": user.avatar_url,
            "child_name": user.child_name,
            "child_grade": user.child_grade,
            "serverchan_key": user.serverchan_key,
        },
    }


@router.put("/profile")
async def update_profile(
    body: UpdateProfileBody,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """更新用户信息"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    updates = body.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(user, field, value)

    user.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(user)

    return {
        "code": 0,
        "data": {
            "id": user.id,
            "nickname": user.nickname,
            "child_name": user.child_name,
            "child_grade": user.child_grade,
            "serverchan_key": user.serverchan_key,
        },
    }
