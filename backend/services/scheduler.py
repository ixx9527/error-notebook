from datetime import date

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select

from models.database import async_session
from models.review_plan import ReviewPlan
from models.error_question import ErrorQuestion
from models.user import User
from services.notifier import send_notification, format_reminder_message
from services.wx_subscribe import consume_and_send

scheduler = AsyncIOScheduler()

REVIEW_REMINDER_TEMPLATE = "tmpl_review_reminder_1"


async def daily_review_reminder():
    """每天早上 8:00 检查今日待复习，发送提醒"""
    today = date.today()

    async with async_session() as session:
        result = await session.execute(
            select(ReviewPlan, ErrorQuestion)
            .join(ErrorQuestion, ReviewPlan.question_id == ErrorQuestion.id)
            .where(
                ReviewPlan.review_date == today,
                ReviewPlan.status == "pending",
            )
        )
        rows = result.all()

        if not rows:
            return

        user_items: dict[int, list[dict]] = {}
        for plan, question in rows:
            if plan.user_id not in user_items:
                user_items[plan.user_id] = []
            user_items[plan.user_id].append({
                "subject": question.subject,
                "topic": question.topic,
            })

        user_ids = list(user_items.keys())
        users_result = await session.execute(
            select(User).where(User.id.in_(user_ids))
        )
        users = {u.id: u for u in users_result.scalars().all()}

    for user_id, items in user_items.items():
        message = format_reminder_message(items, str(today))
        user = users.get(user_id)
        if not user:
            continue

        sent = False
        if user.openid:
            subject_counts = {}
            for item in items:
                subj = item.get("subject", "其他")
                subject_counts[subj] = subject_counts.get(subj, 0) + 1
            thing1 = "、".join(f"{k}{v}道" for k, v in subject_counts.items())

            sent = await consume_and_send(
                user_id,
                REVIEW_REMINDER_TEMPLATE,
                data={
                    "thing1": {"value": thing1[:20]},
                    "time2": {"value": f"{today} 08:00"},
                    "thing3": {"value": f"共{len(items)}道错题待复习"[0:20]},
                },
                page="pages/review/review",
            )

        if not sent:
            serverchan_key = user.serverchan_key if user else None
            await send_notification("错题复习提醒", message, serverchan_key=serverchan_key)


scheduler.add_job(daily_review_reminder, CronTrigger(hour=8, minute=0), id="daily_review_reminder")
