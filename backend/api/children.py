from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from deps import get_db, get_current_user_id
from models.child import Child

router = APIRouter()


class ChildBody(BaseModel):
    name: str
    grade: str | None = None


@router.get("")
async def list_children(
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    result = await db.execute(
        select(Child).where(Child.user_id == user_id).order_by(Child.created_at)
    )
    children = result.scalars().all()
    return {
        "code": 0,
        "data": [{"id": c.id, "name": c.name, "grade": c.grade} for c in children],
    }


@router.post("")
async def create_child(
    body: ChildBody,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    child = Child(user_id=user_id, name=body.name, grade=body.grade)
    db.add(child)
    await db.commit()
    await db.refresh(child)
    return {"code": 0, "data": {"id": child.id, "name": child.name, "grade": child.grade}}


@router.put("/{child_id}")
async def update_child(
    child_id: int,
    body: ChildBody,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    result = await db.execute(
        select(Child).where(Child.id == child_id, Child.user_id == user_id)
    )
    child = result.scalar_one_or_none()
    if not child:
        raise HTTPException(404, "孩子不存在")

    child.name = body.name
    if body.grade is not None:
        child.grade = body.grade
    await db.commit()
    await db.refresh(child)
    return {"code": 0, "data": {"id": child.id, "name": child.name, "grade": child.grade}}


@router.delete("/{child_id}")
async def delete_child(
    child_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    result = await db.execute(
        select(Child).where(Child.id == child_id, Child.user_id == user_id)
    )
    child = result.scalar_one_or_none()
    if not child:
        raise HTTPException(404, "孩子不存在")

    await db.delete(child)
    await db.commit()
    return {"code": 0, "message": "已删除"}
