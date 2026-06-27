import os
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from deps import get_db, get_current_user_id
from models.error_question import ErrorQuestion
from models.review_plan import ReviewPlan
from services.qwen_vl import analyze_error_image_async
from services.image_processor import save_upload, preprocess_image
from services.ebbinghaus import generate_review_plans
from config import MAX_IMAGE_SIZE_BYTES

router = APIRouter()


class UpdateErrorBody(BaseModel):
    model_config = {"extra": "forbid"}

    subject: str | None = None
    topic: str | None = None
    question_text: str | None = None
    formulas: list | None = None
    figures: list | None = None
    student_answer: str | None = None
    correct_answer: str | None = None
    error_type: str | None = None
    error_analysis: str | None = None
    tags: list | None = None


ALLOWED_IMAGE_EXTS = {"jpg", "jpeg", "png", "webp"}


@router.post("/upload")
async def upload_error(
    image: UploadFile = File(...),
    subject: str | None = Form(None),
    note: str | None = Form(None),
    child_id: int | None = Form(None),
    do_perspective: bool = Form(False),
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """上传错题图片，调用 Qwen-VL 识别并存储"""
    ext = image.filename.rsplit(".", 1)[-1].lower() if "." in image.filename else "jpg"
    if ext not in ALLOWED_IMAGE_EXTS:
        raise HTTPException(status_code=400, detail=f"不支持的图片格式：{ext}，仅支持 {', '.join(ALLOWED_IMAGE_EXTS)}")

    file_content = await image.read()
    if len(file_content) > MAX_IMAGE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"图片过大，最大允许 {MAX_IMAGE_SIZE_BYTES // (1024 * 1024)}MB",
        )

    image_path = save_upload(file_content, ext)

    processed_path = preprocess_image(image_path, do_perspective=do_perspective)

    results = await analyze_error_image_async(processed_path)
    if not results:
        raise HTTPException(status_code=500, detail="图片识别失败，请重试")

    saved_questions = []
    for item in results:
        q = ErrorQuestion(
            user_id=user_id,
            child_id=child_id,
            subject=subject or item.get("subject", "其他"),
            topic=item.get("topic"),
            question_text=item.get("question_text", ""),
            formulas=item.get("formulas"),
            figures=item.get("figures"),
            student_answer=item.get("student_answer"),
            correct_answer=item.get("correct_answer"),
            error_type=item.get("error_type"),
            error_analysis=item.get("error_analysis"),
            tags=item.get("tags"),
            original_image=image_path,
            processed_image=processed_path if processed_path != image_path else None,
        )
        db.add(q)
        await db.flush()

        plans = generate_review_plans(q.id, user_id)
        for p in plans:
            db.add(ReviewPlan(**p))

        saved_questions.append({
            "id": q.id,
            "subject": q.subject,
            "topic": q.topic,
            "question_text": q.question_text,
            "formulas": q.formulas,
            "figures": q.figures,
            "student_answer": q.student_answer,
            "correct_answer": q.correct_answer,
            "error_type": q.error_type,
            "error_analysis": q.error_analysis,
            "tags": q.tags,
            "review_plans": plans,
        })

    await db.commit()
    return {"code": 0, "data": saved_questions}


@router.post("/upload/async")
async def upload_error_async(
    image: UploadFile = File(...),
    subject: str | None = Form(None),
    note: str | None = Form(None),
    do_perspective: bool = Form(False),
    user_id: int = Depends(get_current_user_id),
):
    """异步上传：立即返回 task_id，后台处理 Qwen-VL 识别"""
    ext = image.filename.rsplit(".", 1)[-1].lower() if "." in image.filename else "jpg"
    if ext not in ALLOWED_IMAGE_EXTS:
        raise HTTPException(status_code=400, detail=f"不支持的图片格式：{ext}")

    file_content = await image.read()
    if len(file_content) > MAX_IMAGE_SIZE_BYTES:
        raise HTTPException(status_code=400, detail=f"图片过大，最大允许 {MAX_IMAGE_SIZE_BYTES // (1024 * 1024)}MB")

    image_path = save_upload(file_content, ext)

    from services.task_queue import create_task
    task_id = create_task(image_path, user_id, subject, do_perspective)

    return {"code": 0, "data": {"task_id": task_id, "status": "pending"}}


@router.get("/upload/status/{task_id}")
async def upload_status(task_id: str):
    """查询异步上传任务状态"""
    from services.task_queue import get_task
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    resp = {
        "task_id": task["task_id"],
        "status": task["status"],
        "created_at": task["created_at"],
    }
    if task["status"] == "completed":
        resp["data"] = task["results"]
    elif task["status"] == "failed":
        resp["error"] = task["error"]

    return {"code": 0, "data": resp}


@router.get("")
async def list_errors(
    subject: str | None = Query(None),
    tag: str | None = Query(None),
    child_id: int | None = Query(None),
    status: str = Query("active"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """错题列表，支持按科目/标签/孩子筛选"""
    query = select(ErrorQuestion).where(
        ErrorQuestion.user_id == user_id,
        ErrorQuestion.status == status,
    )
    if subject:
        query = query.where(ErrorQuestion.subject == subject)
    if tag:
        query = query.where(ErrorQuestion.tags.contains([tag]))
    if child_id:
        query = query.where(ErrorQuestion.child_id == child_id)

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar()

    query = query.order_by(ErrorQuestion.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "code": 0,
        "data": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [_question_to_dict(q) for q in items],
        },
    }


@router.get("/{question_id}")
async def get_error(
    question_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """错题详情"""
    q = await _get_user_question(db, question_id, user_id)
    return {"code": 0, "data": _question_to_dict(q)}


@router.put("/{question_id}")
async def update_error(
    question_id: int,
    body: UpdateErrorBody,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """修改错题（手动纠正）"""
    q = await _get_user_question(db, question_id, user_id)

    updates = body.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(q, field, value)

    q.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(q)
    return {"code": 0, "data": _question_to_dict(q)}


@router.delete("/{question_id}")
async def delete_error(
    question_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """软删除错题"""
    q = await _get_user_question(db, question_id, user_id)
    q.status = "deleted"
    await db.commit()
    return {"code": 0, "message": "已删除"}


async def _get_user_question(db: AsyncSession, question_id: int, user_id: int) -> ErrorQuestion:
    result = await db.execute(
        select(ErrorQuestion).where(
            ErrorQuestion.id == question_id,
            ErrorQuestion.user_id == user_id,
            ErrorQuestion.status != "deleted",
        )
    )
    q = result.scalar_one_or_none()
    if not q:
        raise HTTPException(status_code=404, detail="错题不存在")
    return q


def _question_to_dict(q: ErrorQuestion) -> dict:
    return {
        "id": q.id,
        "subject": q.subject,
        "topic": q.topic,
        "question_text": q.question_text,
        "formulas": q.formulas,
        "figures": q.figures,
        "student_answer": q.student_answer,
        "correct_answer": q.correct_answer,
        "error_type": q.error_type,
        "error_analysis": q.error_analysis,
        "tags": q.tags,
        "original_image": q.original_image,
        "processed_image": q.processed_image,
        "status": q.status,
        "created_at": str(q.created_at) if q.created_at else None,
        "updated_at": str(q.updated_at) if q.updated_at else None,
    }
