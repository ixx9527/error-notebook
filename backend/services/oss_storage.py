import os
import uuid
import httpx
import hmac
import hashlib
import base64
from datetime import datetime, timezone

from config import (
    OSS_ACCESS_KEY_ID,
    OSS_ACCESS_KEY_SECRET,
    OSS_BUCKET,
    OSS_ENDPOINT,
    UPLOAD_DIR,
)


def _is_oss_enabled() -> bool:
    return bool(OSS_ACCESS_KEY_ID and OSS_ACCESS_KEY_SECRET and OSS_BUCKET and OSS_ENDPOINT)


def _sign(method: str, object_key: str, content_type: str = "") -> dict:
    """生成 OSS V1 签名 headers"""
    date = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
    resource = f"/{OSS_BUCKET}/{object_key}"

    string_to_sign = f"{method}\n\n{content_type}\n{date}\n{resource}"
    signature = base64.b64encode(
        hmac.new(
            OSS_ACCESS_KEY_SECRET.encode(),
            string_to_sign.encode(),
            hashlib.sha1,
        ).digest()
    ).decode()

    host = f"{OSS_BUCKET}.{OSS_ENDPOINT}"
    return {
        "Authorization": f"OSS {OSS_ACCESS_KEY_ID}:{signature}",
        "Date": date,
        "Host": host,
    }


async def upload_to_oss(local_path: str, object_key: str | None = None) -> str:
    """上传文件到 OSS，返回访问 URL。如果 OSS 未配置则返回本地路径"""
    if not _is_oss_enabled():
        return local_path

    if object_key is None:
        ext = os.path.splitext(local_path)[1]
        object_key = f"errors/{datetime.now().strftime('%Y/%m')}/{uuid.uuid4().hex}{ext}"

    with open(local_path, "rb") as f:
        file_data = f.read()

    content_type = "image/jpeg"
    if local_path.endswith(".png"):
        content_type = "image/png"
    elif local_path.endswith(".webp"):
        content_type = "image/webp"

    headers = _sign("PUT", object_key, content_type)
    headers["Content-Type"] = content_type
    url = f"https://{OSS_BUCKET}.{OSS_ENDPOINT}/{object_key}"

    async with httpx.AsyncClient() as client:
        resp = await client.put(url, content=file_data, headers=headers, timeout=30)
        if resp.status_code not in (200, 201):
            raise RuntimeError(f"OSS 上传失败: {resp.status_code} {resp.text}")

    return url


async def delete_from_oss(url: str) -> bool:
    """从 OSS 删除文件"""
    if not _is_oss_enabled():
        return False

    object_key = url.split(f"{OSS_BUCKET}.{OSS_ENDPOINT}/")[-1]
    headers = _sign("DELETE", object_key)

    async with httpx.AsyncClient() as client:
        resp = await client.delete(
            f"https://{OSS_BUCKET}.{OSS_ENDPOINT}/{object_key}",
            headers=headers,
            timeout=10,
        )
        return resp.status_code in (200, 204)


def get_oss_url(object_key: str) -> str:
    """获取 OSS 文件的访问 URL"""
    if not _is_oss_enabled():
        return ""
    return f"https://{OSS_BUCKET}.{OSS_ENDPOINT}/{object_key}"
