import httpx

from config import SERVERCHAN_DEFAULT_KEY, WECOM_BOT_WEBHOOK


async def send_via_serverchan(send_key: str, title: str, message: str) -> bool:
    """通过 Server酱 推送到微信"""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"https://sctapi.ftqq.com/{send_key}.send",
                data={"title": title, "desp": message},
            )
            return resp.status_code == 200
    except Exception:
        return False


async def send_via_wecom_bot(webhook_url: str, message: str) -> bool:
    """通过企业微信群机器人推送"""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                webhook_url,
                json={"msgtype": "text", "text": {"content": message}},
            )
            return resp.status_code == 200
    except Exception:
        return False


async def send_notification(title: str, message: str, serverchan_key: str | None = None) -> bool:
    """统一通知入口，优先 Server酱，兜底企业微信"""
    key = serverchan_key or SERVERCHAN_DEFAULT_KEY
    if key:
        ok = await send_via_serverchan(key, title, message)
        if ok:
            return True

    if WECOM_BOT_WEBHOOK:
        return await send_via_wecom_bot(WECOM_BOT_WEBHOOK, message)

    return False


def format_reminder_message(items: list[dict], review_date: str) -> str:
    """格式化复习提醒消息"""
    subject_counts: dict[str, int] = {}
    for item in items:
        subj = item.get("subject", "其他")
        subject_counts[subj] = subject_counts.get(subj, 0) + 1

    subject_str = "、".join(f"{k}{v}道" for k, v in subject_counts.items())
    return f"📚 今日复习提醒（{review_date}）\n共有 {len(items)} 道错题待复习：{subject_str}\n\n点击查看详情并开始复习"
