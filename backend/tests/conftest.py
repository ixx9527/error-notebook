import os
import jwt
import pytest
from unittest.mock import patch
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

os.environ["DATABASE_URL"] = "sqlite+aiosqlite://"

from models.database import Base
from models.user import User
from models.child import Child
from models.error_question import ErrorQuestion
from models.review_plan import ReviewPlan
from models.subscribe_message import SubscribeMessage
from deps import get_db, JWT_SECRET

engine = create_async_engine("sqlite+aiosqlite://", echo=False)
TestSession = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session() -> AsyncSession:
    async with TestSession() as session:
        yield session


@pytest.fixture
async def client(db_session: AsyncSession):
    from main import app

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    user = User(openid="test_openid_001", nickname="测试用户", child_name="小明", child_grade="三年级")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def auth_token(test_user: User) -> str:
    from datetime import datetime, timedelta, timezone
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {"user_id": test_user.id, "exp": now + timedelta(days=30), "iat": now},
        JWT_SECRET,
        algorithm="HS256",
    )


@pytest.fixture
def auth_headers(auth_token: str) -> dict:
    return {"Authorization": f"Bearer {auth_token}"}


MOCK_QWEN_RESULT = [
    {
        "subject": "数学",
        "topic": "三位数乘法",
        "question_text": "小红有235本书，又买了12本，一共多少本？",
        "formulas": ["$235 + 12 = ?$"],
        "figures": [],
        "student_answer": "247",
        "correct_answer": "247",
        "error_type": "计算错误",
        "error_analysis": "计算过程有涂改，建议巩固进位加法。",
        "tags": ["进位加法", "三位数"],
    }
]


@pytest.fixture
def mock_qwen_vl():
    with patch("api.errors.analyze_error_image_async", return_value=MOCK_QWEN_RESULT) as m:
        yield m
