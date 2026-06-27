from datetime import datetime

from sqlalchemy import String, Text, DateTime, ForeignKey, Index, func, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from models.database import Base

_JSONB = JSONB().with_variant(JSON, "sqlite")


class ErrorQuestion(Base):
    __tablename__ = "error_questions"
    __table_args__ = (
        Index("idx_error_questions_user_subject", "user_id", "subject", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    child_id: Mapped[int | None] = mapped_column(ForeignKey("children.id", ondelete="SET NULL"))
    subject: Mapped[str] = mapped_column(String(32), nullable=False)
    topic: Mapped[str | None] = mapped_column(String(128))
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    formulas: Mapped[dict | None] = mapped_column(_JSONB)
    figures: Mapped[dict | None] = mapped_column(_JSONB)
    student_answer: Mapped[str | None] = mapped_column(Text)
    correct_answer: Mapped[str | None] = mapped_column(Text)
    error_type: Mapped[str | None] = mapped_column(String(64))
    error_analysis: Mapped[str | None] = mapped_column(Text)
    tags: Mapped[list | None] = mapped_column(_JSONB)

    original_image: Mapped[str] = mapped_column(Text, nullable=False)
    processed_image: Mapped[str | None] = mapped_column(Text)

    status: Mapped[str] = mapped_column(String(32), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
