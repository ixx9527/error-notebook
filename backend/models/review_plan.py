from datetime import datetime, date

from sqlalchemy import Integer, String, Date, DateTime, ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column

from models.database import Base


class ReviewPlan(Base):
    __tablename__ = "review_plans"
    __table_args__ = (
        Index("idx_review_plans_user_date", "user_id", "review_date", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("error_questions.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    child_id: Mapped[int | None] = mapped_column(ForeignKey("children.id", ondelete="SET NULL"))
    review_date: Mapped[date] = mapped_column(Date, nullable=False)
    review_round: Mapped[int] = mapped_column(Integer, nullable=False)
    interval_days: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)
    mastery_level: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
