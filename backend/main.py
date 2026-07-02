import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import UPLOAD_DIR


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    from models.database import engine, Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    from services.scheduler import scheduler
    scheduler.start()
    yield
    scheduler.shutdown()


_is_dev = os.getenv("ENV", "production") != "production"

app = FastAPI(
    title="错题本 API",
    lifespan=lifespan,
    docs_url="/docs" if _is_dev else None,
    redoc_url="/redoc" if _is_dev else None,
    openapi_url="/openapi.json" if _is_dev else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

from api import auth, errors, review, export, stats, users, notify, children  # noqa: E402

app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(errors.router, prefix="/api/errors", tags=["错题管理"])
app.include_router(review.router, prefix="/api/review", tags=["复习管理"])
app.include_router(export.router, prefix="/api/export", tags=["PDF导出"])
app.include_router(stats.router, prefix="/api/stats", tags=["统计"])
app.include_router(users.router, prefix="/api/users", tags=["用户"])
app.include_router(notify.router, prefix="/api/notify", tags=["消息通知"])
app.include_router(children.router, prefix="/api/children", tags=["孩子管理"])


@app.get("/health")
async def health():
    return {"status": "ok"}
