import asyncio
import uuid
from datetime import datetime
from enum import Enum

from models.database import async_session
from models.error_question import ErrorQuestion
from models.review_plan import ReviewPlan
from services.qwen_vl import analyze_error_image_async
from services.image_processor import preprocess_image
from services.ebbinghaus import generate_review_plans
from services.oss_storage import upload_to_oss, _is_oss_enabled


class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


_tasks: dict[str, dict] = {}


def create_task(image_path: str, user_id: int, subject: str | None, do_perspective: bool) -> str:
    task_id = uuid.uuid4().hex
    _tasks[task_id] = {
        "task_id": task_id,
        "status": TaskStatus.PENDING,
        "user_id": user_id,
        "image_path": image_path,
        "subject": subject,
        "do_perspective": do_perspective,
        "results": None,
        "error": None,
        "created_at": datetime.utcnow().isoformat(),
    }
    asyncio.create_task(_process_task(task_id))
    return task_id


def get_task(task_id: str) -> dict | None:
    return _tasks.get(task_id)


async def _process_task(task_id: str):
    task = _tasks.get(task_id)
    if not task:
        return

    task["status"] = TaskStatus.PROCESSING

    try:
        image_path = task["image_path"]
        processed_path = preprocess_image(image_path, do_perspective=task["do_perspective"])

        results = await analyze_error_image_async(processed_path)
        if not results:
            task["status"] = TaskStatus.FAILED
            task["error"] = "图片识别失败，请重试"
            return

        saved = []
        async with async_session() as session:
            for item in results:
                original = image_path
                processed = processed_path if processed_path != image_path else None

                if _is_oss_enabled():
                    try:
                        original = await upload_to_oss(image_path)
                        if processed and processed != image_path:
                            processed = await upload_to_oss(processed_path)
                    except Exception:
                        pass

                q = ErrorQuestion(
                    user_id=task["user_id"],
                    subject=task["subject"] or item.get("subject", "其他"),
                    topic=item.get("topic"),
                    question_text=item.get("question_text", ""),
                    formulas=item.get("formulas"),
                    figures=item.get("figures"),
                    student_answer=item.get("student_answer"),
                    correct_answer=item.get("correct_answer"),
                    error_type=item.get("error_type"),
                    error_analysis=item.get("error_analysis"),
                    tags=item.get("tags"),
                    original_image=original,
                    processed_image=processed,
                )
                session.add(q)
                await session.flush()

                plans = generate_review_plans(q.id, task["user_id"])
                for p in plans:
                    session.add(ReviewPlan(**p))

                saved.append({
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

            await session.commit()

        task["status"] = TaskStatus.COMPLETED
        task["results"] = saved

    except Exception as e:
        task["status"] = TaskStatus.FAILED
        task["error"] = str(e)


def cleanup_old_tasks(max_age_hours: int = 24):
    cutoff = datetime.utcnow().timestamp() - max_age_hours * 3600
    to_remove = [
        tid for tid, t in _tasks.items()
        if datetime.fromisoformat(t["created_at"]).timestamp() < cutoff
    ]
    for tid in to_remove:
        del _tasks[tid]
