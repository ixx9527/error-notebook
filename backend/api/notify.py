from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from deps import get_db, get_current_user_id
from models.user import User
from services.wx_subscribe import record_subscription

router = APIRouter()


class SubscribeBody(BaseModel):
    template_ids: list[str]


@router.post("/subscribe")
async def subscribe(
    body: SubscribeBody,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """记录用户订阅消息授权（前端弹窗授权后调用）"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return {"code": 0, "message": "用户不存在"}

    await record_subscription(user_id, user.openid, body.template_ids)
    return {"code": 0, "message": "订阅成功"}
