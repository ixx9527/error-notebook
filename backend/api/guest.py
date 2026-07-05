import time
from collections import defaultdict

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from deps import get_db
from services.qwen_vl import analyze_error_image_async
from services.image_processor import save_upload, preprocess_image
from config import MAX_IMAGE_SIZE_BYTES, GUEST_DEMO_LIMIT_PER_HOUR

router = APIRouter()

ALLOWED_IMAGE_EXTS = {"jpg", "jpeg", "png", "webp"}

_rate_limit: dict[str, list[float]] = defaultdict(list)


def _check_rate_limit(ip: str) -> bool:
    now = time.time()
    window = _rate_limit[ip]
    _rate_limit[ip] = [t for t in window if now - t < 3600]
    if len(_rate_limit[ip]) >= GUEST_DEMO_LIMIT_PER_HOUR:
        return False
    _rate_limit[ip].append(now)
    return True


@router.post("/demo-upload")
async def guest_demo_upload(
    request: Request,
    image: UploadFile = File(...),
    subject: str | None = Form(None),
    do_perspective: bool = Form(False),
):
    """游客体验：上传照片进行 AI 识别，仅返回结果，不保存数据"""
    ip = request.client.host if request.client else "unknown"
    if not _check_rate_limit(ip):
        raise HTTPException(status_code=429, detail="体验次数已达上限，请注册后使用完整功能")

    ext = image.filename.rsplit(".", 1)[-1].lower() if "." in image.filename else "jpg"
    if ext not in ALLOWED_IMAGE_EXTS:
        raise HTTPException(status_code=400, detail=f"不支持的图片格式：{ext}")

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

    demo_results = []
    for item in results:
        demo_results.append({
            "subject": subject or item.get("subject", "其他"),
            "topic": item.get("topic"),
            "question_text": item.get("question_text", ""),
            "formulas": item.get("formulas"),
            "figures": item.get("figures"),
            "student_answer": item.get("student_answer"),
            "correct_answer": item.get("correct_answer"),
            "error_type": item.get("error_type"),
            "error_analysis": item.get("error_analysis"),
            "tags": item.get("tags"),
        })

    return {"code": 0, "data": demo_results}
