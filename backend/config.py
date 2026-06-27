import os
from dotenv import load_dotenv

load_dotenv()

# 数据库
DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost:5432/error_notebook")

# Qwen-VL
DASHSCOPE_API_KEY: str = os.getenv("DASHSCOPE_API_KEY", "")
QWEN_VL_MODEL: str = "qwen-vl-max"

# 微信小程序
WX_APPID: str = os.getenv("WX_APPID", "")
WX_SECRET: str = os.getenv("WX_SECRET", "")

# Server酱
SERVERCHAN_DEFAULT_KEY: str = os.getenv("SERVERCHAN_DEFAULT_KEY", "")

# 企业微信机器人
WECOM_BOT_WEBHOOK: str = os.getenv("WECOM_BOT_WEBHOOK", "")

# 文件存储
UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")

# 图片处理
MAX_IMAGE_DIMENSION: int = 1920
MAX_IMAGE_SIZE_BYTES: int = 1 * 1024 * 1024  # 1MB

# OSS（可选）
OSS_ACCESS_KEY_ID: str = os.getenv("OSS_ACCESS_KEY_ID", "")
OSS_ACCESS_KEY_SECRET: str = os.getenv("OSS_ACCESS_KEY_SECRET", "")
OSS_BUCKET: str = os.getenv("OSS_BUCKET", "")
OSS_ENDPOINT: str = os.getenv("OSS_ENDPOINT", "")
