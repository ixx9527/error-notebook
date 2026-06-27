from datetime import datetime, timedelta, timezone

import httpx
import jwt
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from deps import get_db
from models.user import User
from config import WX_APPID, WX_SECRET

router = APIRouter()

JWT_SECRET = WX_SECRET or "dev-secret"
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_DAYS = 30


@router.post("/login")
async def login(code: str, db: AsyncSession = Depends(get_db)):
    """微信登录：code 换取 openid，创建或返回用户"""
    url = (
        f"https://api.weixin.qq.com/sns/jscode2session"
        f"?appid={WX_APPID}&secret={WX_SECRET}"
        f"&js_code={code}&grant_type=authorization_code"
    )

    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        data = resp.json()

    openid = data.get("openid")
    if not openid:
        raise HTTPException(status_code=400, detail="微信登录失败")

    result = await db.execute(select(User).where(User.openid == openid))
    user = result.scalar_one_or_none()

    if not user:
        user = User(openid=openid)
        db.add(user)
        await db.commit()
        await db.refresh(user)

    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {"user_id": user.id, "exp": now + timedelta(days=JWT_EXPIRE_DAYS), "iat": now},
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )

    return {
        "code": 0,
        "data": {
            "token": token,
            "user_id": user.id,
            "nickname": user.nickname,
            "child_name": user.child_name,
        },
    }
