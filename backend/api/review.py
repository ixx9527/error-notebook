from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from deps import get_db, get_current_user_id
from models.review_plan import ReviewPlan
from models.error_question import ErrorQuestion
from services.ebbinghaus import get_next_review_date

router = APIRouter()


@router.get("/today")
async def get_today_review(
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """今日待复习列表"""
    today = date.today()
    result = await db.execute(
        select(ReviewPlan, ErrorQuestion)
        .join(ErrorQuestion, ReviewPlan.question_id == ErrorQuestion.id)
        .where(
            ReviewPlan.user_id == user_id,
            ReviewPlan.review_date == today,
            ReviewPlan.status == "pending",
        )
    )
    rows = result.all()

    items = [
        {
            "plan_id": plan.id,
            "question_id": q.id,
            "subject": q.subject,
            "topic": q.topic,
            "question_text": q.question_text,
            "review_round": plan.review_round,
            "interval_days": plan.interval_days,
            "created_at": str(q.created_at) if q.created_at else None,
        }
        for plan, q in rows
    ]

    return {"code": 0, "data": {"date": str(today), "total": len(items), "items": items}}


@router.get("/upcoming")
async def get_upcoming_review(
    days: int = Query(7, ge=1, le=30),
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """未来 N 天复习计划"""
    today = date.today()
    end_date = today + timedelta(days=days)

    result = await db.execute(
        select(ReviewPlan, ErrorQuestion)
        .join(ErrorQuestion, ReviewPlan.question_id == ErrorQuestion.id)
        .where(
            ReviewPlan.user_id == user_id,
            ReviewPlan.review_date.between(today, end_date),
            ReviewPlan.status == "pending",
        )
        .order_by(ReviewPlan.review_date)
    )
    rows = result.all()

    items = [
        {
            "plan_id": plan.id,
            "question_id": plan.question_id,
            "review_date": str(plan.review_date),
            "review_round": plan.review_round,
            "interval_days": plan.interval_days,
            "subject": q.subject,
            "topic": q.topic,
        }
        for plan, q in rows
    ]

    return {"code": 0, "data": items}


class CompleteReviewBody(BaseModel):
    mastery_level: int = Field(ge=1, le=5, description="掌握程度 1-5")


@router.post("/{plan_id}/complete")
async def complete_review(
    plan_id: int,
    body: CompleteReviewBody,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """完成复习，计算下一轮复习日期"""
    result = await db.execute(
        select(ReviewPlan).where(ReviewPlan.id == plan_id, ReviewPlan.user_id == user_id)
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="复习计划不存在")

    plan.status = "completed"
    plan.completed_at = datetime.utcnow()
    plan.mastery_level = body.mastery_level

    next_review = get_next_review_date(plan.question_id, plan.review_round, body.mastery_level)
    if next_review:
        next_plan = ReviewPlan(**next_review)
        db.add(next_plan)

    await db.commit()

    return {
        "code": 0,
        "message": "复习完成",
        "data": {"next_review": next_review},
    }
