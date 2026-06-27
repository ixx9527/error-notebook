import io
import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


# --- 认证相关 ---

@pytest.mark.asyncio
async def test_list_errors_unauthorized(client):
    resp = await client.get("/api/errors")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_today_review_unauthorized(client):
    resp = await client.get("/api/review/today")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_expired_token_rejected(client, test_user):
    import jwt
    from datetime import datetime, timedelta, timezone
    from deps import JWT_SECRET

    now = datetime.now(timezone.utc)
    expired = jwt.encode(
        {"user_id": test_user.id, "exp": now - timedelta(days=1), "iat": now - timedelta(days=31)},
        JWT_SECRET,
        algorithm="HS256",
    )
    resp = await client.get("/api/errors", headers={"Authorization": f"Bearer {expired}"})
    assert resp.status_code == 401
    assert "过期" in resp.json()["detail"]


# --- 错题 CRUD ---

@pytest.mark.asyncio
async def test_upload_and_list(client, auth_headers, mock_qwen_vl):
    fake_image = b"\xff\xd8\xff\xe0" + b"\x00" * 100  # minimal JPEG header

    resp = await client.post(
        "/api/errors/upload",
        files={"image": ("test.jpg", io.BytesIO(fake_image), "image/jpeg")},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["code"] == 0
    assert len(data["data"]) == 1
    assert data["data"][0]["subject"] == "数学"
    assert data["data"][0]["topic"] == "三位数乘法"
    question_id = data["data"][0]["id"]

    # 列表应包含刚上传的题
    resp = await client.get("/api/errors", headers=auth_headers)
    assert resp.status_code == 200
    items = resp.json()["data"]["items"]
    assert len(items) == 1
    assert items[0]["id"] == question_id

    # 详情
    resp = await client.get(f"/api/errors/{question_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["question_text"] == "小红有235本书，又买了12本，一共多少本？"


@pytest.mark.asyncio
async def test_upload_rejects_bad_ext(client, auth_headers):
    resp = await client.post(
        "/api/errors/upload",
        files={"image": ("test.exe", io.BytesIO(b"data"), "application/octet-stream")},
        headers=auth_headers,
    )
    assert resp.status_code == 400
    assert "格式" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_upload_rejects_oversized(client, auth_headers):
    big_data = b"\x00" * (2 * 1024 * 1024)  # 2MB
    resp = await client.post(
        "/api/errors/upload",
        files={"image": ("big.jpg", io.BytesIO(big_data), "image/jpeg")},
        headers=auth_headers,
    )
    assert resp.status_code == 400
    assert "过大" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_update_error(client, auth_headers, mock_qwen_vl):
    fake_image = b"\xff\xd8\xff\xe0" + b"\x00" * 100
    resp = await client.post(
        "/api/errors/upload",
        files={"image": ("test.jpg", io.BytesIO(fake_image), "image/jpeg")},
        headers=auth_headers,
    )
    qid = resp.json()["data"][0]["id"]

    resp = await client.put(
        f"/api/errors/{qid}",
        json={"subject": "英语", "topic": "语法填空", "error_analysis": "已修正"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    d = resp.json()["data"]
    assert d["subject"] == "英语"
    assert d["topic"] == "语法填空"
    assert d["error_analysis"] == "已修正"
    # 未传的字段保持原值
    assert d["question_text"] == "小红有235本书，又买了12本，一共多少本？"


@pytest.mark.asyncio
async def test_update_error_rejects_bad_field(client, auth_headers, mock_qwen_vl):
    fake_image = b"\xff\xd8\xff\xe0" + b"\x00" * 100
    resp = await client.post(
        "/api/errors/upload",
        files={"image": ("test.jpg", io.BytesIO(fake_image), "image/jpeg")},
        headers=auth_headers,
    )
    qid = resp.json()["data"][0]["id"]

    resp = await client.put(
        f"/api/errors/{qid}",
        json={"nonexistent_field": "value"},
        headers=auth_headers,
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_delete_error(client, auth_headers, mock_qwen_vl):
    fake_image = b"\xff\xd8\xff\xe0" + b"\x00" * 100
    resp = await client.post(
        "/api/errors/upload",
        files={"image": ("test.jpg", io.BytesIO(fake_image), "image/jpeg")},
        headers=auth_headers,
    )
    qid = resp.json()["data"][0]["id"]

    resp = await client.delete(f"/api/errors/{qid}", headers=auth_headers)
    assert resp.status_code == 200

    resp = await client.get(f"/api/errors/{qid}", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_errors_filter_by_subject(client, auth_headers, mock_qwen_vl):
    fake_image = b"\xff\xd8\xff\xe0" + b"\x00" * 100
    await client.post(
        "/api/errors/upload",
        files={"image": ("test.jpg", io.BytesIO(fake_image), "image/jpeg")},
        headers=auth_headers,
    )

    resp = await client.get("/api/errors?subject=数学", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["total"] == 1

    resp = await client.get("/api/errors?subject=英语", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["total"] == 0


# --- 复习管理 ---

@pytest.mark.asyncio
async def test_today_review_empty(client, auth_headers):
    resp = await client.get("/api/review/today", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["total"] == 0


@pytest.mark.asyncio
async def test_upcoming_review(client, auth_headers):
    resp = await client.get("/api/review/upcoming?days=7", headers=auth_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json()["data"], list)


@pytest.mark.asyncio
async def test_complete_review_mastery_validation(client, auth_headers):
    resp = await client.post(
        "/api/review/99999/complete",
        json={"mastery_level": 0},
        headers=auth_headers,
    )
    assert resp.status_code == 422

    resp = await client.post(
        "/api/review/99999/complete",
        json={"mastery_level": 6},
        headers=auth_headers,
    )
    assert resp.status_code == 422


# --- 用户资料 ---

@pytest.mark.asyncio
async def test_get_and_update_profile(client, auth_headers):
    resp = await client.get("/api/users/profile", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["nickname"] == "测试用户"

    resp = await client.put(
        "/api/users/profile",
        json={"child_name": "小红", "child_grade": "四年级", "serverchan_key": "SCT123"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    d = resp.json()["data"]
    assert d["child_name"] == "小红"
    assert d["child_grade"] == "四年级"
    assert d["serverchan_key"] == "SCT123"


# --- 统计 ---

@pytest.mark.asyncio
async def test_stats_summary(client, auth_headers, mock_qwen_vl):
    fake_image = b"\xff\xd8\xff\xe0" + b"\x00" * 100
    await client.post(
        "/api/errors/upload",
        files={"image": ("test.jpg", io.BytesIO(fake_image), "image/jpeg")},
        headers=auth_headers,
    )

    resp = await client.get("/api/stats/summary", headers=auth_headers)
    assert resp.status_code == 200
    d = resp.json()["data"]
    assert d["total_questions"] == 1
    assert "by_subject" in d
