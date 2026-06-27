import os
import uuid

import cv2
import numpy as np

from config import UPLOAD_DIR, MAX_IMAGE_DIMENSION


def compress_image(image: np.ndarray, max_dim: int = MAX_IMAGE_DIMENSION) -> np.ndarray:
    """压缩图片尺寸"""
    h, w = image.shape[:2]
    if max(h, w) <= max_dim:
        return image
    scale = max_dim / max(h, w)
    return cv2.resize(image, (int(w * scale), int(h * scale)))


def order_points(pts: np.ndarray) -> np.ndarray:
    """将四个点按 左上、右上、右下、左下 排序"""
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect


def correct_perspective(image: np.ndarray) -> np.ndarray:
    """梯形矫正，如果未检测到四边形则返回原图"""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(gray, 75, 200)

    contours, _ = cv2.findContours(edged, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]

    screen_cnt = None
    for c in contours:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        if len(approx) == 4:
            screen_cnt = approx
            break

    if screen_cnt is None:
        return image

    pts = screen_cnt.reshape(4, 2)
    rect = order_points(pts)
    (tl, tr, br, bl) = rect

    width = max(
        int(np.sqrt((br[0] - bl[0]) ** 2 + (br[1] - bl[1]) ** 2)),
        int(np.sqrt((tr[0] - tl[0]) ** 2 + (tr[1] - tl[1]) ** 2)),
    )
    height = max(
        int(np.sqrt((tr[0] - br[0]) ** 2 + (tr[1] - br[1]) ** 2)),
        int(np.sqrt((tl[0] - bl[0]) ** 2 + (tl[1] - bl[1]) ** 2)),
    )

    dst = np.array([[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]], dtype="float32")
    matrix = cv2.getPerspectiveTransform(rect, dst)
    return cv2.warpPerspective(image, matrix, (width, height))


def save_upload(file_content: bytes, ext: str) -> str:
    """保存上传文件，返回文件路径"""
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(file_content)
    return filepath


def preprocess_image(image_path: str, do_perspective: bool = False) -> str:
    """图片预处理：压缩 + 可选梯形矫正，返回处理后路径"""
    img = cv2.imread(image_path)
    if img is None:
        return image_path

    img = compress_image(img)

    if do_perspective:
        img = correct_perspective(img)

    base, ext = os.path.splitext(image_path)
    output_path = f"{base}_processed{ext}"
    cv2.imwrite(output_path, img)
    return output_path
