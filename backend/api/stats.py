from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, cast, Date

from deps import get_db, get_current_user_id
from models.error_question import ErrorQuestion
from models.review_plan import ReviewPlan

router = APIRouter()


@router.get("/summary")
async def get_stats_summary(
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """统计概览"""
    # 错题总数
    total_q = (await db.execute(
        select(func.count()).select_from(ErrorQuestion).where(
            ErrorQuestion.user_id == user_id,
            ErrorQuestion.status == "active",
        )
    )).scalar()

    # 按科目统计
    subject_result = await db.execute(
        select(ErrorQuestion.subject, func.count())
        .where(ErrorQuestion.user_id == user_id, ErrorQuestion.status == "active")
        .group_by(ErrorQuestion.subject)
    )
    by_subject = {row[0]: row[1] for row in subject_result.all()}

    # 按错因统计
    error_type_result = await db.execute(
        select(ErrorQuestion.error_type, func.count())
        .where(ErrorQuestion.user_id == user_id, ErrorQuestion.status == "active", ErrorQuestion.error_type.isnot(None))
        .group_by(ErrorQuestion.error_type)
    )
    by_error_type = {row[0]: row[1] for row in error_type_result.all()}

    # 复习完成率
    total_plans = (await db.execute(
        select(func.count()).select_from(ReviewPlan).where(ReviewPlan.user_id == user_id)
    )).scalar() or 0

    completed_plans = (await db.execute(
        select(func.count()).select_from(ReviewPlan).where(
            ReviewPlan.user_id == user_id,
            ReviewPlan.status == "completed",
        )
    )).scalar() or 0

    review_rate = round(completed_plans / total_plans * 100, 1) if total_plans > 0 else 0

    return {
        "code": 0,
        "data": {
            "total_questions": total_q,
            "by_subject": by_subject,
            "by_error_type": by_error_type,
            "review_total": total_plans,
            "review_completed": completed_plans,
            "review_rate": review_rate,
        },
    }


@router.get("/trend")
async def get_trend(
    days: int = Query(30, ge=7, le=90),
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """每日错题录入趋势（最近 N 天）"""
    start_date = date.today() - timedelta(days=days - 1)

    result = await db.execute(
        select(cast(ErrorQuestion.created_at, Date), func.count())
        .where(
            ErrorQuestion.user_id == user_id,
            ErrorQuestion.status == "active",
            ErrorQuestion.created_at >= start_date,
        )
        .group_by(cast(ErrorQuestion.created_at, Date))
        .order_by(cast(ErrorQuestion.created_at, Date))
    )
    daily = {str(row[0]): row[1] for row in result.all()}

    trend = []
    for i in range(days):
        d = start_date + timedelta(days=i)
        trend.append({"date": str(d), "count": daily.get(str(d), 0)})

    return {"code": 0, "data": trend}


@router.get("/mastery")
async def get_mastery_distribution(
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """掌握程度分布（1-5 星）"""
    result = await db.execute(
        select(ReviewPlan.mastery_level, func.count())
        .where(
            ReviewPlan.user_id == user_id,
            ReviewPlan.mastery_level.isnot(None),
        )
        .group_by(ReviewPlan.mastery_level)
        .order_by(ReviewPlan.mastery_level)
    )
    distribution = {level: count for level, count in result.all()}

    labels = {1: "完全不会", 2: "比较生疏", 3: "基本掌握", 4: "比较熟练", 5: "完全掌握"}
    data = [
        {"level": level, "label": labels.get(level, ""), "count": distribution.get(level, 0)}
        for level in range(1, 6)
    ]

    return {"code": 0, "data": data}
