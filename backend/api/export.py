from datetime import date, datetime, timedelta
import calendar

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from deps import get_db, get_current_user_id
from models.error_question import ErrorQuestion
from models.review_plan import ReviewPlan

router = APIRouter()


@router.get("/pdf")
async def export_pdf(
    ids: str | None = Query(None, description="逗号分隔的题目ID"),
    subject: str | None = Query(None),
    tags: str | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """导出错题 PDF"""
    if date_from:
        try:
            datetime.strptime(date_from, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="date_from 格式应为 YYYY-MM-DD")
    if date_to:
        try:
            datetime.strptime(date_to, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="date_to 格式应为 YYYY-MM-DD")

    query = select(ErrorQuestion).where(
        ErrorQuestion.user_id == user_id,
        ErrorQuestion.status == "active",
    )

    if ids:
        id_list = [int(x) for x in ids.split(",")]
        query = query.where(ErrorQuestion.id.in_(id_list))
    if subject:
        query = query.where(ErrorQuestion.subject == subject)
    if tags:
        tag_list = tags.split(",")
        query = query.where(ErrorQuestion.tags.contains(tag_list))
    if date_from:
        query = query.where(ErrorQuestion.created_at >= datetime.strptime(date_from, "%Y-%m-%d"))
    if date_to:
        query = query.where(ErrorQuestion.created_at < datetime.strptime(date_to, "%Y-%m-%d") + timedelta(days=1))

    result = await db.execute(query.order_by(ErrorQuestion.created_at.desc()))
    questions = result.scalars().all()

    if not questions:
        raise HTTPException(status_code=404, detail="没有找到符合条件的错题")

    try:
        from services.pdf_exporter import render_pdf
        pdf_bytes = render_pdf(questions, date.today())
    except ImportError:
        raise HTTPException(status_code=501, detail="PDF 导出功能尚未实现（需要 weasyprint）")

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=error_notebook_{date.today()}.pdf"},
    )


@router.get("/monthly-report")
async def export_monthly_report(
    year: int = Query(None),
    month: int = Query(None),
    child_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """导出月度报告 PDF"""
    today = date.today()
    year = year or today.year
    month = month or today.month

    first_day = date(year, month, 1)
    last_day = date(year, month, calendar.monthrange(year, month)[1])

    query = select(ErrorQuestion).where(
        ErrorQuestion.user_id == user_id,
        ErrorQuestion.status == "active",
        ErrorQuestion.created_at >= datetime.combine(first_day, datetime.min.time()),
        ErrorQuestion.created_at < datetime.combine(last_day + timedelta(days=1), datetime.min.time()),
    )
    if child_id:
        query = query.where(ErrorQuestion.child_id == child_id)

    result = await db.execute(query.order_by(ErrorQuestion.created_at))
    questions = result.scalars().all()

    review_query = select(func.count()).select_from(ReviewPlan).where(
        ReviewPlan.user_id == user_id,
        ReviewPlan.review_date >= first_day,
        ReviewPlan.review_date <= last_day,
        ReviewPlan.status == "completed",
    )
    if child_id:
        review_query = review_query.where(ReviewPlan.child_id == child_id)

    completed_reviews = (await db.execute(review_query)).scalar() or 0

    if not questions:
        raise HTTPException(status_code=404, detail=f"{year}年{month}月没有错题记录")

    try:
        from services.pdf_exporter import render_monthly_report
        pdf_bytes = render_monthly_report(
            questions=questions,
            year=year,
            month=month,
            completed_reviews=completed_reviews,
        )
    except ImportError:
        raise HTTPException(status_code=501, detail="PDF 导出功能尚未实现")

    filename = f"monthly_report_{year}_{month:02d}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
