from datetime import datetime, timedelta, timezone

import httpx
import jwt
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from deps import get_db
from models.user import User
from config import WX_APPID, WX_SECRET
from services.security import hash_password, verify_password

router = APIRouter()

JWT_SECRET = WX_SECRET or "dev-secret"
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_DAYS = 30


class RegisterBody(BaseModel):
    username: str
    password: str

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3 or len(v) > 32:
            raise ValueError("用户名长度需在 3-32 个字符之间")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 6 or len(v) > 64:
            raise ValueError("密码长度需在 6-64 个字符之间")
        return v


class AccountLoginBody(BaseModel):
    username: str
    password: str


def _create_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {"user_id": user_id, "exp": now + timedelta(days=JWT_EXPIRE_DAYS), "iat": now},
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )


def _auth_response(user: User) -> dict:
    return {
        "code": 0,
        "data": {
            "token": _create_token(user.id),
            "user_id": user.id,
            "nickname": user.nickname,
            "child_name": user.child_name,
        },
    }


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

    return _auth_response(user)


@router.post("/register")
async def register(body: RegisterBody, db: AsyncSession = Depends(get_db)):
    """账号密码注册"""
    result = await db.execute(select(User).where(User.username == body.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="用户名已存在")

    user = User(username=body.username, password_hash=hash_password(body.password))
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return _auth_response(user)


@router.post("/login/account")
async def account_login(body: AccountLoginBody, db: AsyncSession = Depends(get_db)):
    """账号密码登录"""
    result = await db.execute(select(User).where(User.username == body.username))
    user = result.scalar_one_or_none()

    if not user or not user.password_hash or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=400, detail="用户名或密码错误")

    return _auth_response(user)
