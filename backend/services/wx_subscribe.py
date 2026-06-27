import httpx
from sqlalchemy import select

from models.database import async_session
from models.user import User
from models.subscribe_message import SubscribeMessage
from config import WX_APPID, WX_SECRET

_access_token_cache: dict = {"token": None, "expires_at": 0}


async def _get_access_token() -> str:
    """获取微信 access_token，带内存缓存"""
    import time

    if _access_token_cache["token"] and time.time() < _access_token_cache["expires_at"]:
        return _access_token_cache["token"]

    url = (
        "https://api.weixin.qq.com/cgi-bin/token"
        f"?grant_type=client_credential&appid={WX_APPID}&secret={WX_SECRET}"
    )

    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        data = resp.json()

    token = data.get("access_token")
    if not token:
        raise RuntimeError(f"获取 access_token 失败: {data}")

    _access_token_cache["token"] = token
    _access_token_cache["expires_at"] = time.time() + data.get("expires_in", 7200) - 300
    return token


async def record_subscription(user_id: int, openid: str, template_ids: list[str]):
    """记录用户的订阅消息授权"""
    async with async_session() as session:
        for tmpl_id in template_ids:
            sub = SubscribeMessage(
                user_id=user_id,
                openid=openid,
                template_id=tmpl_id,
                status="active",
            )
            session.add(sub)
        await session.commit()


async def send_subscribe_message(
    openid: str,
    template_id: str,
    data: dict,
    page: str = "",
) -> bool:
    """发送一条订阅消息"""
    try:
        token = await _get_access_token()
        url = f"https://api.weixin.qq.com/cgi-bin/message/subscribe/send?access_token={token}"

        payload = {
            "touser": openid,
            "template_id": template_id,
            "data": data,
        }
        if page:
            payload["page"] = page

        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload)
            result = resp.json()

        if result.get("errcode") == 0:
            return True

        return False
    except Exception:
        return False


async def consume_and_send(
    user_id: int,
    template_id: str,
    data: dict,
    page: str = "",
) -> bool:
    """消耗一条订阅额度并发送消息（一次性订阅模式）"""
    async with async_session() as session:
        result = await session.execute(
            select(SubscribeMessage).where(
                SubscribeMessage.user_id == user_id,
                SubscribeMessage.template_id == template_id,
                SubscribeMessage.status == "active",
            ).limit(1)
        )
        sub = result.scalar_one_or_none()
        if not sub:
            return False

        sub.status = "used"
        await session.commit()

    return await send_subscribe_message(sub.openid, template_id, data, page)
